#!/usr/local/bin/python

import argparse
import os
import re

from github import Github, Repository, PullRequest, Commit
from typing import List, Optional


CHANGELOG_LABELS = [
    "changelog/bugfix",
    "changelog/breaking",
    "changelog/enhancement",
    "changelog/feature",
    "changelog/internal",
    "changelog/ignore",
    "changelog/feature",
    "changelog/security",
]

CHANGELOG_CATEGORIES = {
    "changelog/breaking": "Breaking Changes",
    "changelog/enhancement": "Enhancements",
    "changelog/feature": "Features",
    "changelog/bugfix": "Fixed",
    "changelog/internal": "Internal",
    "changelog/feature": "Feature",
    "changelog/feature",
}

REPO_NAME = "dbt-labs/dbt-cloud"

MERGE_MSG_REGEX = re.compile(
    r"^Merge pull request #(?P<pr_number>\d+) from (?:\S)*\n\n(?P<pr_title>.*)$"
)

BASE_SQUASH_MSG_REGEX = re.compile(
    r"^(?P<base_msg>.*)"
)

SQUASH_MSG_REGEX = re.compile(
    r"^(?P<pr_title>.*) \(#(?P<pr_number>\d+)\).*$", re.DOTALL
)


def get_pr_labels(pull) -> List[str]:
    """
    Given a pull request, returns all of the labels on that PR.
    """
    return [label.name for label in pull.labels]


def get_changelog_label(pull) -> Optional[str]:
    """
    Returns the first changelog label found for a given PR.
    """
    labels = get_pr_labels(pull)
    to_return = None

    for label in labels:
        if label in CHANGELOG_LABELS:
            # just use the first label found for generation
            return label

    return None


def get_pr_number(commit_msg: str) -> Optional[int]:
    result = re.match(MERGE_MSG_REGEX, commit_msg)

    if not result:
        return None

    return int(result.group(1))


def get_commits(repo, branch: str):
    import pprint

    for commit in repo.get_commits():
        pprint.pprint(commit.commit.message)

    return []


def ci_pr(pull) -> bool:
    """
    Returns true if the pull request specified has one of the changelog labels,
    false if it doesn't have one of the labels.
    """
    labels = get_pr_labels(pull)
    count = 0

    for label in labels:
        if label in CHANGELOG_LABELS:
            count += 1

    if count == 1:
        return True

    elif count > 1:
        print("Failed: more than one matching changelog label.")
        return False

    else:
        print("Failed: no matching changelog labels found.")
        return False


def get_args():
    parser = argparse.ArgumentParser(description="Get args.")
    parser.add_argument(
        "--ci-pr",
        required=False,
        help=(
            "Given a PR number, run a CI process on that PR. If the PR has "
            "the right label, CI will pass. If it has the wrong set of labels "
            "then CI will fail."
        ),
    )

    parser.add_argument(
        "--start-sha",
        required=False,
        help=(
            "Given a sha, find all merge commits since that SHA, and generate "
            "a changelog for them."
        ),
    )

    args = parser.parse_args()
    return args


def run_ci(args):
    """
    Main function for the CI process.
    """
    pr_number = int(args.ci_pr)

    github_instance = Github(os.getenv("GITHUB_ACCESS_TOKEN"))
    repo = github_instance.get_repo(REPO_NAME)

    pull = repo.get_pull(pr_number)

    return ci_pr(pull)


def _get_changelog_entries(repo, start_sha):
    entries = []

    for commit in repo.get_commits():
        if commit.sha == start_sha:
            break

        # parse title and pr number for normal merge format
        result = MERGE_MSG_REGEX.match(commit.commit.message)

        # check for squash and merge format
        if not result:
            # parse first line from commit message
            first_line = BASE_SQUASH_MSG_REGEX.match(commit.commit.message)
            # parse title and pr number from squash and merge first line
            result = SQUASH_MSG_REGEX.match(first_line.group("base_msg"))

        if result:
            pr_number = int(result.group("pr_number"))

            entries.append(
                {
                    "label": get_changelog_label(repo.get_pull(pr_number)),
                    "title": result.group("pr_title"),
                }
            )

    return entries


def run_changelog_generation(args):
    """
    Main function for the changelog generation process.
    """
    github_instance = Github(os.getenv("GITHUB_ACCESS_TOKEN"))
    repo = github_instance.get_repo(REPO_NAME)

    entries = _get_changelog_entries(repo, args.start_sha)
    output = ""

    for label, category in CHANGELOG_CATEGORIES.items():
        has_entries = False
        category_output = f"\n#### {category}\n\n"

        for entry in entries:
            if label == entry["label"]:
                has_entries = True
                title = entry["title"]
                category_output += f"- {title}\n"

        if has_entries:
            output += category_output

    print(output)


if __name__ == "__main__":
    args = get_args()

    if args.ci_pr:
        if run_ci(args):
            exit(0)
        else:
            exit(1)

    else:
        run_changelog_generation(args)
        exit(0)
