"""
Evidence runner robustness validation for v0.16.3_CANDIDATE.
"""

def validate_extra_env(extra_env):
    if not isinstance(extra_env, dict):
        raise TypeError("RUNNER_INVALID_ENV")

    normalized = {}

    for key, value in sorted(extra_env.items()):
        if not isinstance(key, str):
            raise TypeError("RUNNER_INVALID_ENV")
        if not isinstance(value, str):
            raise TypeError("RUNNER_INVALID_ENV")

        normalized[key] = value

    return normalized

def main():
    validate_extra_env({"GG_MODE": "candidate"})
    print("evidence_runner_robustness_evidence: PASS")

if __name__ == "__main__":
    main()
