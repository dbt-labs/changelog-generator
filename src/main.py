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
    "changelog/internal",
    "changelog/ignore",
]

REPO_NAME = "fishtown-analytics/dbt-cloud"

MERGE_MSG_REGEX = re.compile(r"^Merge pull request #(\d+) from ")


def get_pr_labels(pull: PullRequest) -> List[str]:
    """
    Given a pull request, returns all of the labels on that PR.
    """
    return [label.name for label in pull.labels]


def get_changelog_label(pull: PullRequest) -> Optional[str]:
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


def get_commits(repo: Repository, branch: str):
    import pprint

    for commit in repo.get_commits():
        pprint.pprint(commit.commit.message)

    return []


def ci_pr(pull: PullRequest) -> bool:
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
        required=True,
        help=(
            "Given a PR number, run a CI process on that PR. If the PR has "
            "the right label, CI will pass. If it has the wrong set of labels "
            "then CI will fail."
        ),
    )

    args = parser.parse_args()
    return args


def run_ci(args):
    """
    Main function for the CI process.
    """
    pr_number = int(args.ci_pr)

    github_instance = Github(access_token)
    repo = github_instance.get_repo(REPO_NAME)

    pull = repo.get_pull(pr_number)

    return ci_pr(pull)


def run_changelog_generation(args):
    """
    Main function for the changelog generation process.
    """
    pass


if __name__ == "__main__":
    args = get_args()

    access_token = os.getenv("GITHUB_TOKEN")

    github_instance = Github(access_token)
    repo = github_instance.get_repo(REPO_NAME)

    print(get_commits(repo, "master"))
    exit(0)

    if args.ci_pr:
        if run_ci(args):
            exit(0)
        else:
            exit(1)

    else:
        run_changelog_generation(args)
        exit(0)
