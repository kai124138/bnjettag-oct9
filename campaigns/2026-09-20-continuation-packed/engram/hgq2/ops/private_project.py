#!/usr/bin/env python3
"""Verify project privacy; --create-private is the only mutating mode.

Credentials come from WANDB_API_KEY or the existing kai-wandb Kubernetes secret
and are never printed or written. No project invitations or public links are made.
"""
import argparse
import base64
import json
import os
import subprocess
import urllib.request

ENTITY = 'kayamaguchi-uc-san-diego'
PROJECT = 'BNJetTag-Engram-Experimental'


def graphql(query, variables, key=None):
    headers = {'Content-Type': 'application/json'}
    if key:
        headers['Authorization'] = 'Basic ' + base64.b64encode(('api:' + key).encode()).decode()
    request = urllib.request.Request('https://api.wandb.ai/graphql',
        data=json.dumps({'query': query, 'variables': variables}).encode(), headers=headers)
    with urllib.request.urlopen(request, timeout=45) as response:
        result = json.load(response)
    if result.get('errors'):
        raise RuntimeError(json.dumps(result['errors']))
    return result['data']


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--create-private', action='store_true')
    args = parser.parse_args()
    key = os.environ.get('WANDB_API_KEY')
    if not key:
        encoded = subprocess.check_output(['kubectl', '-n', 'cms-ml', 'get', 'secret',
            'kai-wandb', '-o', 'jsonpath={.data.WANDB_API_KEY}'], text=True).strip()
        key = base64.b64decode(encoded).decode().strip()
    if not key:
        raise RuntimeError('No W&B credential available')
    variables = {'entity': ENTITY, 'name': PROJECT}
    query = '''query ($entity: String!, $name: String!) {
      project(name: $name, entityName: $entity) { name access }
    }'''
    project = graphql(query, variables, key)['project']
    if project is None and args.create_private:
        graphql('''mutation ($entity: String!, $name: String!) {
          upsertModel(input: {name: $name, entityName: $entity, access: "PRIVATE",
            description: "Exploratory Engram-inspired jet memory pilot. Accuracy first; compute and memory costs reported separately. Validation screening only."}) {
            model { name access }
          }
        }''', variables, key)
        project = graphql(query, variables, key)['project']
    if project is None or project['access'] != 'PRIVATE':
        raise RuntimeError('Separate Engram project does not exist with PRIVATE access; refusing training')
    # Independently ensure anonymous GraphQL requests cannot return project data.
    try:
        anonymous = graphql(query, variables)['project']
    except (urllib.error.HTTPError, RuntimeError):
        anonymous = None
    if anonymous is not None:
        raise RuntimeError('Anonymous project read unexpectedly succeeded')
    print(json.dumps({'project': PROJECT, 'entity': ENTITY, 'access': project['access'],
                      'anonymous_read': 'denied', 'url': f'https://wandb.ai/{ENTITY}/{PROJECT}'}))


if __name__ == '__main__':
    main()
