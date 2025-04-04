import importlib.util
import datetime
import os
import numpy as np
import random
import inspect

def detect_hardcoded(src: str, expected_output) -> bool:
    """
    Detect if expected output is directly returned or hardcoded in source.
    Works for primitives, lists, tuples, dicts, and np.array.
    """
    try:
        flat = src.replace(" ", "").replace("\n", "").lower()

        if isinstance(expected_output, np.ndarray):
            values = expected_output.tolist()
            return all(str(v) in flat for v in values)

        elif isinstance(expected_output, (list, tuple)):
            return all(str(v) in flat for v in expected_output)

        elif isinstance(expected_output, dict):
            return all(str(k) in flat and str(v) in flat for k, v in expected_output.items())

        elif isinstance(expected_output, (int, float, str)):
            return f"return{repr(expected_output)}".lower() in flat

    except Exception as e:
        print(f"[Hardcoded detection error] {e}")

    return False

def run_randomized_checks(analyzer) -> dict:
    failures = {}

    try:
        # create_performance_array
        rand = [random.randint(60, 100) for _ in range(6)]
        expected = np.array(rand)
        result = analyzer.create_performance_array(rand)
        if not isinstance(result, np.ndarray) or not np.array_equal(result, expected):
            failures["create_performance_array"] = "Randomized logic failed"
    except:
        failures["create_performance_array"] = "Exception occurred"

    try:
        # validate_scores
        arr = np.array([60, 75, 100])
        if not analyzer.validate_scores(arr):
            failures["validate_scores"] = "Randomized logic failed"
    except:
        failures["validate_scores"] = "Exception occurred"

    try:
        # compute_performance_summary
        arr = np.array([70, 80, 90])
        expected = (240, 80.0, 90)
        result = analyzer.compute_performance_summary(arr)
        if not isinstance(result, tuple) or not all(round(a, 1) == round(b, 1) for a, b in zip(result, expected)):
            failures["compute_performance_summary"] = "Randomized logic failed"
    except:
        failures["compute_performance_summary"] = "Exception occurred"

    try:
        # apply_bonus
        arr = np.array([84, 90, 95])
        expected = np.round(np.clip(arr * np.where(arr > 85, 1.05, 1), None, 100), 1)
        result = np.round(analyzer.apply_bonus(arr), 1)
        if not np.allclose(result, expected):
            failures["apply_bonus"] = "Randomized logic failed"
    except:
        failures["apply_bonus"] = "Exception occurred"

    try:
        # categorize_employees
        arr = np.array([91, 85, 60])
        expected = np.array(["Excellent", "Good", "Needs Improvement"])
        result = analyzer.categorize_employees(arr)
        if not np.array_equal(result, expected):
            failures["categorize_employees"] = "Randomized logic failed"
    except:
        failures["categorize_employees"] = "Exception occurred"

    try:
        # format_scores_with_grades
        arr = np.array([91, 85, 73, 60])
        expected = np.array(["A", "B", "C", "D"])
        result = analyzer.format_scores_with_grades(arr)
        if not np.array_equal(result, expected):
            failures["format_scores_with_grades"] = "Randomized logic failed"
    except:
        failures["format_scores_with_grades"] = "Exception occurred"

    return failures

def test_student_code(solution_path):
    report_dir = os.path.join(os.path.dirname(__file__), "..", "student_workspace")
    report_path = os.path.join(report_dir, "report.txt")
    os.makedirs(report_dir, exist_ok=True)

    spec = importlib.util.spec_from_file_location("student_module", solution_path)
    student_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(student_module)

    Analyzer = student_module.EmployeePerformanceAnalyzer
    analyzer = Analyzer()

    report_lines = [f"\n=== Test Run at {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ==="]

    # Visible test cases
    visible_tests = [
        {
            "desc": "Create Step Array",
            "func": "create_performance_array",
            "input": [85, 90, 78, 92, 88],
            "expected": np.array([85, 90, 78, 92, 88])
        },
        {
            "desc": "Validate Step Data - Invalid",
            "func": "validate_scores",
            "input": np.array([85, 90, -5, 110]),
            "expected": False
        },
        {
            "desc": "Compute Performance Summary",
            "func": "compute_performance_summary",
            "input": np.array([85, 90, 78, 92, 88]),
            "expected": (433, 86.6, 92)
        },
        {
            "desc": "Apply Bonus to High Scores",
            "func": "apply_bonus",
            "input": np.array([85, 90, 78, 92, 88]),
            "expected": np.array([85.0, 94.5, 78.0, 96.6, 92.4])
        },
        {
            "desc": "Categorize Employees",
            "func": "categorize_employees",
            "input": np.array([85, 90, 78, 92, 88]),
            "expected": np.array(["Good", "Excellent", "Needs Improvement", "Excellent", "Good"])
        },
        {
            "desc": "Format Score Grades",
            "func": "format_scores_with_grades",
            "input": np.array([90, 80, 65]),
            "expected": np.array(["A", "B", "D"])
        }
    ]

    # Run hidden anti-hardcoding tests
    random_failed_funcs = run_randomized_checks(analyzer)

    # Main test loop
    for i, case in enumerate(visible_tests, 1):
        func = case["func"]
        desc = case["desc"]
        expected = case["expected"]

        try:
            inst = Analyzer()
            method = getattr(inst, func)
            src = inspect.getsource(getattr(Analyzer, func))

            # Anti-cheat checks first
            if "pass" in src and len(src.strip()) < 100:
                msg = f"❌ Test Case {i} Failed ({func}): {desc} | Reason: Function contains only 'pass'"
            elif detect_hardcoded(src, expected):
                msg = f"❌ Test Case {i} Failed ({func}): {desc} | Reason: Hardcoded return detected"
            elif func in random_failed_funcs:
                msg = f"❌ Test Case {i} Failed ({func}): {desc} | Reason: {random_failed_funcs[func]}"
            else:
                result = method(case["input"])

                # Check equality
                if isinstance(expected, np.ndarray):
                    passed = np.array_equal(result, expected)
                elif isinstance(expected, tuple):
                    passed = all(round(a, 2) == round(b, 2) for a, b in zip(result, expected))
                else:
                    passed = result == expected

                if passed:
                    msg = f"✅ Test Case {i} Passed ({func}): {desc}"
                else:
                    msg = f"❌ Test Case {i} Failed ({func}): {desc} | Reason: Incorrect output"

        except Exception as e:
            msg = f"❌ Test Case {i} Crashed ({func}): {desc} | Error: {str(e)}"

        print(msg)
        report_lines.append(msg)

    # Save to file
    with open(report_path, "a", encoding="utf-8") as f:
        f.write("\n".join(report_lines) + "\n")

if __name__ == "__main__":
    solution_file = os.path.join(os.path.dirname(__file__), "..", "student_workspace", "solution.py")
    test_student_code(solution_file)
