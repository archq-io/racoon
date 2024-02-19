#!/bin/bash
# Author: Luka Kovacic <luka.kovacic@archq.io>

if [ -z "$1" ]; then
	echo "Usage: $(basename "$0") output-file"
	exit 1
fi

echo "Creating the release markdown..."

TAG_FIRST=$(git describe --tags --abbrev=0)
TAG_SECOND=$(git describe --tags --abbrev=0 $TAG_FIRST^)

PRETTY_VERSION=${TAG_FIRST:1}

DESCRIPTION_MD="## Release $PRETTY_VERSION | Changelog\n\n";
DESCRIPTION_MD="$DESCRIPTION_MD\`\`\`\n$(git log $TAG_SECOND...$TAG_FIRST --pretty=format:' - %s (%h)\n' --abbrev-commit)\`\`\`";

echo "Writing the release markdown to file $1"
echo -e $DESCRIPTION_MD > $1
