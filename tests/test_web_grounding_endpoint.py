"""
Tes integrasi API untuk memverifikasi alur deep web grounding pada endpoint:
- POST /api/graph/ontology/generate
- POST /api/simulation/create
"""
import io
import os
import sys
import unittest
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../backend')))

from backend.app import create_app
from backend.app.models.project import ProjectManager, ProjectStatus
from backend.app.services.web_research_service import ResearchReport
from backend.app.services.domain_credibility import GroundedFact, EpistemicStatus


class TestWebGroundingEndpoint(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()

    @patch('backend.app.services.ontology_generator.OntologyGenerator.generate')
    @patch('backend.app.services.web_research_service.WebResearchService.research')
    def test_ontology_generate_with_automated_web_grounding(self, mock_research, mock_generate):
        """Memverifikasi bahwa POST /api/graph/ontology/generate secara otomatis menjalankan web research."""
        mock_report = ResearchReport(
            query="Isu terkini terkait pemboikotan produk X",
            credibility_score=0.85,
            summarized_facts=[
                "[VERIFIED] [Score: 0.90 | Domain: kompas.com] Aksi boikot meluas ke platform media sosial."
            ],
            entities_mentioned=[
                {"name": "MerekX", "type": "company"},
                {"name": "Konsumen", "type": "topic"}
            ]
        )

        async def mock_async_research(*args, **kwargs):
            return mock_report

        mock_research.side_effect = mock_async_research

        mock_generate.return_value = {
            "entity_types": [{"name": "Company", "description": "Org", "attributes": [], "examples": []}],
            "edge_types": [{"name": "BOYCOTTS", "description": "Rel", "source_targets": []}],
            "analysis_summary": "Ontologi berhasil dibentuk dengan grounding web"
        }

        # Kirim permintaan multipart
        data = {
            'simulation_requirement': 'Simulasi reaksi warganet terhadap pemboikotan produk X di media sosial.',
            'project_name': 'Proyek Uji Grounding',
            'files': (io.BytesIO(b"Isi dokumen pendukung mengenai krisis PR perusahaan X."), "dokumen_krisis.txt")
        }

        response = self.client.post(
            '/api/graph/ontology/generate',
            data=data,
            content_type='multipart/form-data'
        )

        assert response.status_code == 200, f"Status code {response.status_code}: {response.data}"
        res_json = response.get_json()
        assert res_json["success"] is True
        project_data = res_json["data"]
        project_id = project_data["project_id"]

        # 1. Verifikasi web_research ada di respon API
        assert "web_research" in project_data
        assert project_data["web_research"]["status"] == "COMPLETED"
        assert project_data["web_research"]["credibility_score"] == 0.85

        # 2. Verifikasi metadata tersimpan transparan di objek project
        project = ProjectManager.get_project(project_id)
        assert project is not None
        assert "web_research" in project.metadata
        assert project.metadata["web_research"]["query"]
        assert len(project.metadata["web_research"]["summarized_facts"]) == 1

        # 3. Verifikasi additional_context yang diumpankan ke OntologyGenerator.generate
        assert mock_generate.called
        kwargs = mock_generate.call_args.kwargs
        additional_ctx = kwargs.get('additional_context') or ""
        assert "Hasil Riset Internet Terkini" in additional_ctx
        assert "Aksi boikot meluas" in additional_ctx

        # 4. Verifikasi teks tersimpan di project mencakup bagian grounding
        extracted_text = ProjectManager.get_extracted_text(project_id)
        assert "=== WEB GROUNDING FACTS (SEARXNG) ===" in extracted_text

        # Bersihkan project uji
        ProjectManager.delete_project(project_id)

    @patch('backend.app.services.ontology_generator.OntologyGenerator.generate')
    @patch('backend.app.services.web_research_service.WebResearchService.research')
    def test_ontology_generate_offline_failover(self, mock_research, mock_generate):
        """Memverifikasi bahwa jika SearXNG offline / gagal, alur pembuatan graph tetap berjalan tanpa 500 error."""
        async def mock_async_research_fail(*args, **kwargs):
            raise ConnectionRefusedError("SearXNG instance down")

        mock_research.side_effect = mock_async_research_fail

        mock_generate.return_value = {
            "entity_types": [{"name": "Person", "description": "Person", "attributes": []}],
            "edge_types": [],
            "analysis_summary": "Ontologi fallback"
        }

        data = {
            'simulation_requirement': 'Simulasi demo mahasiswa terkait kebijakan UKT.',
            'project_name': 'Proyek Demo UKT',
            'files': (io.BytesIO(b"Dokumen tuntutan aliansi mahasiswa terkait UKT 2026."), "tuntutan.txt")
        }

        response = self.client.post(
            '/api/graph/ontology/generate',
            data=data,
            content_type='multipart/form-data'
        )

        assert response.status_code == 200, f"Gagal saat offline: {response.data}"
        res_json = response.get_json()
        assert res_json["success"] is True
        project_id = res_json["data"]["project_id"]

        # Verifikasi status OFFLINE_FALLBACK di metadata
        project = ProjectManager.get_project(project_id)
        assert project.metadata["web_research"]["status"] == "OFFLINE_FALLBACK"

        ProjectManager.delete_project(project_id)


if __name__ == '__main__':
    unittest.main()
