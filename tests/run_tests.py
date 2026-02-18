from pathlib import Path
from typing import Dict
from colorama import Fore, Style, init
from tests.validators.html_validator import HTMLValidator

init(autoreset=True)

TEST_MAPPINGS: Dict[str, str] = {
    "index.html": "resources/gens/index.html",
}

CLASS_DEFINITIONS_GROUP_IDS = [
    "sec-core-vocabulary-definition",
    "sec-data-schema-vocabulary-definition",
    "sec-security-vocabulary-definition",
    "sec-hypermedia-vocabulary-definition",
    "sec-default-values",
]


def run_all_tests():
    current_dir = Path(__file__).resolve().parent
    project_root = current_dir.parent
    golden_dir = project_root / "tests" / "manual_goldens" / "html"

    print(f"{Style.BRIGHT}{Fore.BLUE}{'=' * 60}")
    print(f"{Style.BRIGHT}{Fore.BLUE}W3C WOT TOOLCHAIN TEST SUITE")
    print(f"{Style.BRIGHT}{Fore.BLUE}{'=' * 60}\n")

    overall_success = True

    for golden_name, gen_rel_path in TEST_MAPPINGS.items():
        manual_path = golden_dir / golden_name
        generated_path = project_root / gen_rel_path

        if not manual_path.exists():
            print(f"{Fore.RED}[SKIP] Golden validation file not found: {manual_path}")
            continue
        if not generated_path.exists():
            print(f"{Fore.RED}[FAIL] Generated file not found: {generated_path}")
            overall_success = False
            continue

        validator = HTMLValidator(
            manual_path,
            generated_path,
            target_group_ids=CLASS_DEFINITIONS_GROUP_IDS,
        )
        success = validator.validate()
        if not success:
            overall_success = False

    print(f"\n{Style.BRIGHT}{Fore.BLUE}{'=' * 60}")
    if overall_success:
        print(f"{Style.BRIGHT}{Fore.GREEN}OVERALL STATUS: PASSED")
        exit(0)
    else:
        print(f"{Style.BRIGHT}{Fore.RED}OVERALL STATUS: FAILED")
        exit(1)


if __name__ == "__main__":
    run_all_tests()
