import contextlib
import io
import json
import os
import tempfile
import unittest
from pathlib import Path

from creed.apply import apply_creeds
from creed.block import AGENTS_FILENAME, MIRROR_FILENAMES, install_block, validate_block
from creed.cli import main
from creed.profiles import PROFILES, render_block
from creed.validate import validate_repository


class ProfileTests(unittest.TestCase):
    def test_each_creeds_renders_complete_managed_block(self) -> None:
        for profile in PROFILES.values():
            with self.subTest(creed=profile.name):
                block = render_block(profile.name)
                self.assertIn("<!-- creed:managed:start -->", block)
                self.assertIn("## AI-Dependency Creed (Managed)", block)
                self.assertIn(f"- This repository follows the `{profile.name}` creed.", block)
                for directive in profile.directives:
                    self.assertIn(f"- {directive}", block)
                self.assertIn("<!-- creed:managed:end -->", block)


class BlockTests(unittest.TestCase):
    def test_install_block_replaces_existing_block_in_place(self) -> None:
        old_block = render_block("ai-native")
        new_block = render_block("ai-free")
        content = f"# Agents\n\nBefore\n\n{old_block}\n\nAfter\n"
        result = install_block(content, new_block)
        self.assertIn("# Agents", result)
        self.assertIn("Before", result)
        self.assertIn("After", result)
        self.assertNotIn("AI is the foundation of this product.", result)
        self.assertIn(new_block.rstrip("\n"), result)

    def test_install_block_appends_when_no_block_exists(self) -> None:
        block = render_block("ai-augmented")
        content = "# Agents\n\nExisting instruction text.\n"
        result = install_block(content, block)
        self.assertTrue(result.startswith(content))
        self.assertIn(block, result)

    def test_install_block_creates_content_for_missing_agents_file(self) -> None:
        block = render_block("ai-free")
        result = install_block("", block)
        self.assertEqual(result, block)

    def test_validate_block_accepts_correct_block(self) -> None:
        block = render_block("ai-augmented")
        content = f"# Agents\n\n{block}"
        self.assertEqual(validate_block(content, block), [])

    def test_validate_block_detects_missing_block(self) -> None:
        issues = validate_block("# Agents\n", render_block("ai-augmented"))
        self.assertEqual(len(issues), 1)
        self.assertIn("missing", issues[0])

    def test_validate_block_detects_mismatched_block(self) -> None:
        content = f"# Agents\n\n{render_block('ai-native')}"
        issues = validate_block(content, render_block("ai-free"))
        self.assertEqual(len(issues), 1)
        self.assertIn("does not match", issues[0])


class CommandLineTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.previous_directory = os.getcwd()
        os.chdir(self.temporary_directory.name)
        self.root = Path.cwd()

    def tearDown(self) -> None:
        os.chdir(self.previous_directory)
        self.temporary_directory.cleanup()

    def write_configuration(self, creed_name: str = "ai-augmented") -> None:
        (self.root / "CREED.json").write_text(
            json.dumps({"creed": creed_name}, indent=2) + "\n",
            encoding="utf-8",
        )

    def test_apply_creates_agents_file_and_mirrors(self) -> None:
        self.write_configuration()
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            exit_code = main(["apply"])
        self.assertEqual(exit_code, 0)
        agents_content = (self.root / AGENTS_FILENAME).read_text(encoding="utf-8")
        self.assertIn(render_block("ai-augmented"), agents_content)
        for mirror_filename in MIRROR_FILENAMES:
            self.assertEqual(
                (self.root / mirror_filename).read_text(encoding="utf-8"),
                agents_content,
            )

    def test_apply_replaces_old_creeds_block(self) -> None:
        self.write_configuration("ai-augmented")
        (self.root / AGENTS_FILENAME).write_text(
            f"# Agents\n\n{render_block('ai-native')}",
            encoding="utf-8",
        )
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            exit_code = main(["apply"])
        self.assertEqual(exit_code, 0)
        content = (self.root / AGENTS_FILENAME).read_text(encoding="utf-8")
        self.assertIn(render_block("ai-augmented"), content)
        self.assertNotIn(render_block("ai-native"), content)
        for mirror_filename in MIRROR_FILENAMES:
            self.assertEqual(
                (self.root / mirror_filename).read_text(encoding="utf-8"),
                content,
            )

    def test_apply_creeds_flag_overrides_declared_creeds(self) -> None:
        self.write_configuration("ai-augmented")
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            exit_code = main(["apply", "--creed", "ai-free"])
        self.assertEqual(exit_code, 0)
        content = (self.root / AGENTS_FILENAME).read_text(encoding="utf-8")
        self.assertIn(render_block("ai-free"), content)
        self.assertNotIn(render_block("ai-augmented"), content)
        for mirror_filename in MIRROR_FILENAMES:
            self.assertEqual(
                (self.root / mirror_filename).read_text(encoding="utf-8"),
                content,
            )

    def test_validate_passes_for_correct_setup(self) -> None:
        self.write_configuration()
        apply_creeds(self.root)
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            exit_code = main(["validate"])
        self.assertEqual(exit_code, 0)
        self.assertIn("Validation passed", output.getvalue())

    def test_validate_rejects_inconsistent_optional_configuration(self) -> None:
        configuration = {
            "creed": "ai-augmented",
            "crystallization_required": True,
        }
        (self.root / "CREED.json").write_text(
            json.dumps(configuration, indent=2) + "\n",
            encoding="utf-8",
        )
        error_output = io.StringIO()
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(error_output):
            exit_code = main(["validate"])
        self.assertEqual(exit_code, 1)
        self.assertIn("crystallization_required", error_output.getvalue())
        self.assertIn("must be false", error_output.getvalue())

    def test_validate_fails_for_missing_or_stale_block(self) -> None:
        self.write_configuration()
        output = io.StringIO()
        error_output = io.StringIO()
        with contextlib.redirect_stdout(output), contextlib.redirect_stderr(error_output):
            missing_code = main(["validate"])
        self.assertEqual(missing_code, 1)
        self.assertIn("missing", error_output.getvalue())

        apply_creeds(self.root)
        stale_block = render_block("ai-native")
        (self.root / AGENTS_FILENAME).write_text(
            f"# Agents\n\n{stale_block}",
            encoding="utf-8",
        )
        error_output = io.StringIO()
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(error_output):
            stale_code = main(["validate"])
        self.assertEqual(stale_code, 1)
        self.assertIn("does not match", error_output.getvalue())

    def test_validate_fails_when_mirror_is_out_of_sync(self) -> None:
        self.write_configuration()
        apply_creeds(self.root)
        (self.root / "CLAUDE.md").write_text(
            (self.root / "CLAUDE.md").read_text(encoding="utf-8") + "\nDrift\n",
            encoding="utf-8",
        )
        error_output = io.StringIO()
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(error_output):
            exit_code = main(["validate"])
        self.assertEqual(exit_code, 1)
        self.assertIn("CLAUDE.md is not an exact replica", error_output.getvalue())

    def test_list_prints_all_five_creed_names(self) -> None:
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            exit_code = main(["list"])
        self.assertEqual(exit_code, 0)
        listed_output = output.getvalue()
        for creed_name in PROFILES:
            self.assertIn(creed_name, listed_output)
        self.assertEqual(len(PROFILES), 5)

    def test_show_prints_exact_managed_block(self) -> None:
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            exit_code = main(["show", "ai-self-weaning"])
        self.assertEqual(exit_code, 0)
        self.assertEqual(output.getvalue(), render_block("ai-self-weaning"))


class ProjectHygieneTests(unittest.TestCase):
    def test_no_project_file_contains_the_reserved_word(self) -> None:
        reserved_word = "".join(chr(character_code) for character_code in (112, 111, 115, 116, 117, 114, 101))
        project_root = Path(__file__).resolve().parents[1]
        excluded_directories = {".git", "__pycache__", "build", "dist", "feedback", "learnings"}
        excluded_suffixes = {".pyc", ".pyo", ".egg-info"}

        for path in project_root.rglob("*"):
            relative_parts = set(path.relative_to(project_root).parts)
            if relative_parts & excluded_directories:
                continue
            if path.suffix in excluded_suffixes or not path.is_file():
                continue
            file_bytes = path.read_bytes()
            self.assertNotIn(
                reserved_word.encode("utf-8"),
                file_bytes,
                f"A project file contains the reserved word: {path}",
            )


if __name__ == "__main__":
    unittest.main()
