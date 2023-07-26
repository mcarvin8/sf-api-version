This script can be used to check a Salesforce org for the latest metadata API version available.

All Salesforce orgs has its own services URL with all available API versions - `https://org.mysalesforce.com/services/data`

If the `sfdx-project.json` has the latest API version for the org, the script will end.

If the `sfdx-project.json` has an older API version for the org, the Python script will update the JSON file.

The last function in the script uses the GitLab API to create a new branch with the updated `sfdx-project.json`
and then create a merge request from the new branch back into the current branch.

This can be integrated into a Salesforce Org Git branching strategy, where each Salesforce org is assigned a long-running Git branch.

When configuring a scheduled pipeline in GitLab, ensure it's pointing to the org branch and a variable is set with the org's services URL.
