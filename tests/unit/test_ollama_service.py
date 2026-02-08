import pytest
import json
from unittest.mock import patch, MagicMock
from backend.ollama_service import OllamaService

@pytest.fixture
def ollama_service():
    return OllamaService()

@patch('requests.post')
def test_classify_transaction_success(mock_post, ollama_service):
    """Test successful transaction classification"""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.iter_lines.return_value = [
        json.dumps({"response": "Food & Dining", "done": True}).encode('utf-8')
    ]
    mock_post.return_value = mock_response

    category = ollama_service.classify_transaction("Grocery Store buy", 50.0)
    assert category == "Food & Dining"
    mock_post.assert_called_once()

@patch('requests.post')
def test_classify_transaction_invalid_category(mock_post, ollama_service):
    """Test that invalid categories fall back to 'Other'"""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.iter_lines.return_value = [
        json.dumps({"response": "InvalidCategory", "done": True}).encode('utf-8')
    ]
    mock_post.return_value = mock_response

    category = ollama_service.classify_transaction("Unknown purchase", 50.0)
    assert category == "Other"

@patch('requests.post')
def test_classify_transaction_fallback(mock_post, ollama_service):
    """Test fallback model when primary fails"""
    mock_fail = MagicMock()
    mock_fail.status_code = 500
    
    mock_success = MagicMock()
    mock_success.status_code = 200
    mock_success.iter_lines.return_value = [
        json.dumps({"response": "Shopping", "done": True}).encode('utf-8')
    ]
    
    mock_post.side_effect = [mock_fail, mock_success]

    category = ollama_service.classify_transaction("New Shoes", 100.0)
    assert category == "Shopping"
    assert mock_post.call_count >= 2

@patch('requests.post')
def test_classify_transaction_all_models_fail(mock_post, ollama_service):
    """Test that we default to 'Other' when all models fail"""
    mock_fail = MagicMock()
    mock_fail.status_code = 500
    mock_post.return_value = mock_fail

    category = ollama_service.classify_transaction("Test", 100.0)
    assert category == "Other"

@patch('backend.ollama_service.pypdf.PdfReader')
def test_extract_text_from_pdf(mock_pdf_reader, ollama_service):
    """Test PDF text extraction"""
    mock_page = MagicMock()
    mock_page.extract_text.return_value = "Sample text from PDF"
    mock_reader_inst = MagicMock()
    mock_reader_inst.pages = [mock_page]
    mock_pdf_reader.return_value = mock_reader_inst

    with patch('builtins.open', MagicMock()):
        text = ollama_service.extract_text_from_pdf("dummy.pdf")
        assert "Sample text from PDF" in text

@patch('backend.ollama_service.pypdf.PdfReader')
def test_extract_text_from_pdf_error(mock_pdf_reader, ollama_service):
    """Test PDF text extraction error handling"""
    mock_pdf_reader.side_effect = Exception("PDF error")

    with patch('builtins.open', MagicMock()):
        text = ollama_service.extract_text_from_pdf("dummy.pdf")
        assert text is None

@patch('requests.post')
def test_extract_invoice_data(mock_post, ollama_service):
    """Test invoice data extraction"""
    with patch.object(OllamaService, 'extract_text_from_pdf', return_value="Invoice content"):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.iter_lines.return_value = [
            json.dumps({"response": '{"amount": 100.0, "date": "2024-01-01", "vendor": "Test Vendor", "description": "Test"}', "done": True}).encode('utf-8')
        ]
        mock_post.return_value = mock_response

        data = ollama_service.extract_invoice_data("dummy.pdf")
        assert data['amount'] == 100.0
        assert data['vendor'] == "Test Vendor"

@patch('requests.post')
def test_parse_bank_statement(mock_post, ollama_service):
    """Test bank statement parsing"""
    with patch('builtins.open', MagicMock()):
        with patch('backend.ollama_service.pypdf.PdfReader') as mock_pdf_reader:
            # Mock PDF with one page
            mock_page = MagicMock()
            mock_page.extract_text.return_value = "Bank Statement\nDate: 2024-01-01\nAmount: $100"
            mock_reader_inst = MagicMock()
            mock_reader_inst.pages = [mock_page]
            mock_pdf_reader.return_value = mock_reader_inst
            
            # Mock Ollama response
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.iter_lines.return_value = [
                json.dumps({"response": '[{"date": "2024-01-01", "description": "Coffee Shop", "amount": -5.50}]', "done": True}).encode('utf-8')
            ]
            mock_post.return_value = mock_response

            result = ollama_service.parse_bank_statement("dummy.pdf")
            assert "transactions" in result
            assert len(result["transactions"]) == 1
            assert result["transactions"][0]["description"] == "Coffee Shop"

@patch('requests.post')
def test_parse_bank_statement_invalid_json(mock_post, ollama_service):
    """Test bank statement parsing with invalid JSON response"""
    with patch('builtins.open', MagicMock()):
        with patch('backend.ollama_service.pypdf.PdfReader') as mock_pdf_reader:
            mock_page = MagicMock()
            mock_page.extract_text.return_value = "Bank Statement"
            mock_reader_inst = MagicMock()
            mock_reader_inst.pages = [mock_page]
            mock_pdf_reader.return_value = mock_reader_inst
            
            # Mock invalid JSON response
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.iter_lines.return_value = [
                json.dumps({"response": 'invalid json', "done": True}).encode('utf-8')
            ]
            mock_post.return_value = mock_response

            result = ollama_service.parse_bank_statement("dummy.pdf")
            assert "transactions" in result
            assert len(result["transactions"]) == 0
