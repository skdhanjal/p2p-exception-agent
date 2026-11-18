"""Audit IAM for common mistakes. Exit status 1 if anything is found."""

import json
import os
import subprocess
import sys

PROJECT = os.environ["PROJECT_ID"]
REGION = os.environ["REGION"]
PRIMITIVE = {"roles/owner", "roles/editor"}
PAYMENTS_ALLOWED = {
    f"serviceAccount:{os.environ['PAYAGENT_SA']}",
    *[m for m in os.environ.get("PAYMENTS_EXTRA", "").split(",") if m],
}


def gcloud(*args):
    out = subprocess.check_output(["gcloud", *args, "--format=json"], text=True)
    return json.loads(out or "null") or []


def main() -> int:
    findings: list[str] = []
    policy = gcloud("projects", "get-iam-policy", PROJECT)
    for binding in policy.get("bindings", []):
        for member in binding["members"]:
            if member in ("allUsers", "allAuthenticatedUsers"):
                findings.append(f"public member on {binding['role']}")
            if member.startswith("serviceAccount:") and binding["role"] in PRIMITIVE:
                findings.append(f"{member} holds {binding['role']}")

    for account in gcloud("iam", "service-accounts", "list", f"--project={PROJECT}"):
        keys = gcloud(
            "iam",
            "service-accounts",
            "keys",
            "list",
            f"--iam-account={account['email']}",
            "--managed-by=user",
        )
        if keys:
            findings.append(f"user-managed key on {account['email']}")

    for service in gcloud(
        "run", "services", "list", f"--region={REGION}", f"--project={PROJECT}"
    ):
        name = service["metadata"]["name"]
        iam = gcloud(
            "run",
            "services",
            "get-iam-policy",
            name,
            f"--region={REGION}",
            f"--project={PROJECT}",
        )
        for binding in iam.get("bindings", []):
            members = set(binding["members"])
            if members & {"allUsers", "allAuthenticatedUsers"}:
                findings.append(f"{name} is publicly invokable")
            if name == "p2p-payments-mcp" and (binding["role"] == "roles/run.invoker"):
                extra = {
                    m for m in members if m.startswith("serviceAccount:")
                } - PAYMENTS_ALLOWED
                if extra:
                    findings.append(f"unexpected invokers on payments: {sorted(extra)}")

    for finding in findings:
        print("FINDING:", finding)
    print("identity audit:", "FAILED" if findings else "clean")
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
