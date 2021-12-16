import os

import psycopg2
from google.cloud import resourcemanager
from google.cloud import container

DATABASE_HOST = os.getenv('DATABASE_HOST', default='localhost')
DATABASE_PORT = os.getenv('DATABASE_PORT', default=5432)
DATABASE_NAME = os.getenv('DATABASE_NAME', default='grafana_variable_aliases')
DATABASE_USER = os.getenv('DATABASE_USER')
DATABASE_PASSWORD = os.getenv('DATABASE_PASSWORD')

GCP_PROJECTS_QUERY = os.getenv('GCP_PROJECTS_QUERY', default=None)

gcp_perms_to_list_cluster = ['container.clusters.list']

if __name__ == '__main__':
    gcp_projects: list[(str, str, str)] = []
    gcp_clusters: list[(str, str, str, str, str)] = []

    gcp_projects_client = resourcemanager.ProjectsClient()
    gcp_clusters_client = container.ClusterManagerClient()
    # For every project we can see:
    for project in gcp_projects_client.search_projects(query=GCP_PROJECTS_QUERY):
        print(f'In project {project.project_id} ({project.name}):')
        gcp_projects.append((project.project_id, project.display_name, project.name))
        # If we can list clusters:
        if set(gcp_perms_to_list_cluster) == set(gcp_projects_client.test_iam_permissions(
                resource=f'projects/{project.project_id}',
                permissions=gcp_perms_to_list_cluster
        ).permissions):
            # For every cluster we can see:
            for cluster in gcp_clusters_client.list_clusters(
                    parent=f'projects/{project.project_id}/locations/-'
            ).clusters:
                print(f'    Found cluster {cluster.name}')
                gcp_clusters.append(
                    (cluster.name, cluster.location, project.project_id, project.display_name, project.name))

    database_connection = None
    try:
        database_connection = psycopg2.connect(
            host=DATABASE_HOST,
            port=DATABASE_PORT,
            database=DATABASE_NAME,
            user=DATABASE_USER,
            password=DATABASE_PASSWORD
        )
        cursor = database_connection.cursor()
        cursor.execute(
            '''INSERT INTO gcp_project_lookup (project_id, project_display_name, project_api_name) VALUES'''
            + ', '.join([cursor.mogrify('(%s, %s, %s)', x).decode('utf-8') for x in gcp_projects])
            + '''ON CONFLICT (project_id) DO UPDATE SET
                           (project_id, project_display_name, project_api_name) = 
                           (EXCLUDED.project_id, EXCLUDED.project_display_name, EXCLUDED.project_api_name)''')
        cursor.execute(
            '''INSERT INTO gcp_cluster_lookup (cluster_name, cluster_location, project_id, project_display_name, project_api_name) VALUES'''
            + ', '.join([cursor.mogrify('(%s, %s, %s, %s, %s)', x).decode('utf-8') for x in gcp_clusters])
            + '''ON CONFLICT (cluster_name) DO UPDATE SET
                               (cluster_name, cluster_location, project_id, project_display_name, project_api_name) = 
                               (EXCLUDED.cluster_name, EXCLUDED.cluster_location, EXCLUDED.project_id, EXCLUDED.project_display_name, EXCLUDED.project_api_name)''')
        database_connection.commit()
    finally:
        database_connection.close()