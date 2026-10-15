import os
import json
import argparse
import sys
from datetime import datetime
from sqlalchemy import create_engine, text

def migrate(db_uri: str):
    print(f"Connecting to {db_uri}...")
    engine = create_engine(db_uri)

    with engine.connect() as conn:
        # Load extensions and DDL
        schema_path = os.path.join(os.path.dirname(__file__), 'supabase_schema.sql')
        if os.path.exists(schema_path):
            with open(schema_path, 'r') as f:
                schema_sql = f.read()
            # conn.execute(text(schema_sql))
            # print("Schema updated.")

        projects_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'uploads', 'projects')

        success_count = 0
        error_count = 0

        if os.path.exists(projects_dir):
            for proj_id in os.listdir(projects_dir):
                proj_path = os.path.join(projects_dir, proj_id, 'project.json')
                if os.path.isfile(proj_path):
                    try:
                        with open(proj_path, 'r') as f:
                            data = json.load(f)

                        # Map Project data to Supabase format
                        proj_id = data.get('project_id', proj_id)
                        name = data.get('name', 'Untitled')
                        status = data.get('status', 'created')
                        created_at = data.get('created_at', datetime.utcnow().isoformat())
                        updated_at = data.get('updated_at', datetime.utcnow().isoformat())
                        files = json.dumps(data.get('files', []))
                        total_text_length = data.get('total_text_length', 0)
                        ontology = json.dumps(data.get('ontology', {})) if data.get('ontology') else None
                        analysis_summary = data.get('analysis_summary', None)
                        graph_id = data.get('graph_id', None)
                        graph_build_task_id = data.get('graph_build_task_id', None)
                        zep_batch_id = data.get('zep_batch_id', None)
                        zep_batch_operation_id = data.get('zep_batch_operation_id', None)
                        simulation_requirement = data.get('simulation_requirement', None)
                        chunk_size = data.get('chunk_size', 500)
                        chunk_overlap = data.get('chunk_overlap', 50)
                        error_msg = data.get('error', None)

                        upsert_query = text("""
                            INSERT INTO projects (
                                project_id, name, status, created_at, updated_at, files, total_text_length,
                                ontology, analysis_summary, graph_id, graph_build_task_id, zep_batch_id,
                                zep_batch_operation_id, simulation_requirement, chunk_size, chunk_overlap, error
                            ) VALUES (
                                :project_id, :name, :status, :created_at, :updated_at, :files, :total_text_length,
                                :ontology, :analysis_summary, :graph_id, :graph_build_task_id, :zep_batch_id,
                                :zep_batch_operation_id, :simulation_requirement, :chunk_size, :chunk_overlap, :error
                            )
                            ON CONFLICT (project_id) DO UPDATE SET
                                name = EXCLUDED.name,
                                status = EXCLUDED.status,
                                updated_at = EXCLUDED.updated_at,
                                files = EXCLUDED.files,
                                total_text_length = EXCLUDED.total_text_length,
                                ontology = EXCLUDED.ontology,
                                analysis_summary = EXCLUDED.analysis_summary,
                                graph_id = EXCLUDED.graph_id,
                                graph_build_task_id = EXCLUDED.graph_build_task_id,
                                zep_batch_id = EXCLUDED.zep_batch_id,
                                zep_batch_operation_id = EXCLUDED.zep_batch_operation_id,
                                simulation_requirement = EXCLUDED.simulation_requirement,
                                chunk_size = EXCLUDED.chunk_size,
                                chunk_overlap = EXCLUDED.chunk_overlap,
                                error = EXCLUDED.error;
                        """)
                        conn.execute(upsert_query, {
                            "project_id": proj_id, "name": name, "status": status,
                            "created_at": created_at, "updated_at": updated_at, "files": files,
                            "total_text_length": total_text_length, "ontology": ontology,
                            "analysis_summary": analysis_summary, "graph_id": graph_id,
                            "graph_build_task_id": graph_build_task_id, "zep_batch_id": zep_batch_id,
                            "zep_batch_operation_id": zep_batch_operation_id,
                            "simulation_requirement": simulation_requirement, "chunk_size": chunk_size,
                            "chunk_overlap": chunk_overlap, "error": error_msg
                        })
                        success_count += 1

                    except Exception as e:
                        print(f"Error migrating {proj_id}: {e}")
                        error_count += 1
            conn.commit()

    print(f"Migration completed. Successful: {success_count}, Errors: {error_count}")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Migrate local JSON projects to Supabase PostgreSQL.")
    parser.add_argument('--db-uri', type=str, help="Database URI for PostgreSQL.")
    args = parser.parse_args()

    db_uri = args.db_uri or os.environ.get('DATABASE_URI')
    if not db_uri:
        print("DATABASE_URI must be provided either via --db-uri or environment variable.")
        sys.exit(1)

    migrate(db_uri)
