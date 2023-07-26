"""
    The URL should be 'https://org.my.salesforce.com/services/data' depending on your
    Salesforce org.
"""
import argparse
import json
import logging
import os
import sys
import urllib.request
import urllib.parse


# Format logging message
logging.basicConfig(format='%(message)s', level=logging.DEBUG)


def parse_args():
    """
        Function to pass required arguments.
        url - URL with all supported versions
        server - CI Server Host
        project - CI Project ID
        token - access token
        branch - source branch
        file - sfdx-project.json
    """
    parser = argparse.ArgumentParser(description='A script to check the API version.')
    parser.add_argument('-u', '--url')
    parser.add_argument('-s', '--server')
    parser.add_argument('-p', '--project')
    parser.add_argument('-t', '--token')
    parser.add_argument('-b', '--branch')
    parser.add_argument('-f', '--file', default='sfdx-project.json')
    args = parser.parse_args()
    return args


def find_latest_version(url):
    """
        Function to open the URL and find the latest API version.
    """
    with urllib.request.urlopen(url) as json_file:
        data = json.loads(json_file.read().decode('utf8'))

    # Add versions to array, then find highest version
    versions = []
    for element in data:
        # Convert to float first due to decimal
        version = float(element['version'])
        versions.append(version)
    return max(versions)


def check_json_file(json_path):
    """
        Function to check if the JSON file has the latest API version.
    """
    with open(os.path.abspath(json_path), 'r', encoding='utf-8') as file:
        parsed_json = json.load(file)

    source_api_version = parsed_json.get('sourceApiVersion')
    if source_api_version is None:
        logging.info('sourceApiVersion not found in the JSON file.')
        sys.exit(1)
    return parsed_json, source_api_version


def update_json_file(current_version, latest_version, json_path, json_content):
    """
        Function to update the JSON file.
    """
    if str(latest_version) == current_version:
        logging.info('The JSON file already has the latest API version.')
        sys.exit(1)
    else:
        logging.info('The JSON file has an older API version.')
    json_content['sourceApiVersion'] = f'{latest_version}'
    with open(os.path.abspath(json_path), 'w', encoding='utf-8') as file:
        json.dump(json_content, file, indent=2, sort_keys=True)


def send_request(data_request, data_url, token):
    """
        Send a request with urlib.request
        and return the response
    """
    encoded_data = urllib.parse.urlencode(data_request).encode("utf-8")
    formatted_request = urllib.request.Request(data_url, data=encoded_data)
    formatted_request.add_header("PRIVATE-TOKEN", token)

    with urllib.request.urlopen(formatted_request) as request_response:
        logging.info(request_response.read())


def post_to_gitlab(latest_version, json_path, server, project, token, source_branch):
    """
        Function to post the updated JSON to GitLab
        using the GitLab API v4.
    """
    new_branch = f"update_{source_branch}_to_api_version_{latest_version}"

    # Read the content of the json file
    with open(json_path, "r") as json_file:
        content = json_file.read()

    # Update json file on a new branch created from the source branch
    commit_url = f"https://{server}/api/v4/projects/{project}/repository/commits"
    commit_data = {
        "branch": new_branch,
        "start_branch": source_branch,
        "commit_message": f"Update source API version to {latest_version}",
        "actions[][action]": "update",
        "actions[][file_path]": json_path,
        "actions[][content]": content
    }
    send_request(commit_data, commit_url, token)

    # Create merge request back into the source branch
    merge_request_url = f"https://{server}/api/v4/projects/{project}/merge_requests"
    merge_request_data = {
        "source_branch": new_branch,
        "target_branch": source_branch,
        "title": f"Change {source_branch} Source API Version to {latest_version}",
    }
    send_request(merge_request_data, merge_request_url, token)


def main(url, json_path, server, project, token, branch):
    """
        Main function.
    """
    latest_version = find_latest_version(url)

    logging.info('Latest API version: %s', latest_version)
    json_dict, current_version = check_json_file(json_path)
    update_json_file(current_version, latest_version, json_path, json_dict)
    post_to_gitlab(latest_version, json_path, server, project, token, branch)


if __name__ == '__main__':
    inputs = parse_args()
    main(inputs.url, inputs.file,
         inputs.server, inputs.project, inputs.token,
         inputs.branch)
