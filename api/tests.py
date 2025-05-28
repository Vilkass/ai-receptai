import unittest
from unittest.mock import Mock, patch
import io
import re

from api import extract_text_from_pdf, remove_section_between, convert_string_to_history


class TestApyFunctions(unittest.TestCase):

    @patch("api.PdfReader")
    def test_extract_text_from_pdf(self, MockPdfReader):
        # Mock PDF page text
        mock_page = Mock()
        mock_page.extract_text.return_value = (
            "Header\nPacientas:\nJohn Doe\nSveikatos priežiūros įstaigos specialistas:\nDr. Smith\n"
            "Informacija pacientui:\nThis is the content.\nFooter"
        )
        MockPdfReader.return_value.pages = [mock_page]

        # Create a fake PDF file-like object
        fake_pdf = io.BytesIO(b"%PDF-1.4...")

        result = extract_text_from_pdf(fake_pdf)

        # Ensure sensitive sections are removed
        self.assertNotIn("Pacientas:", result)
        self.assertNotIn("John Doe", result)
        self.assertNotIn("Sveikatos priežiūros įstaigos specialistas:", result)
        self.assertIn("Informacija pacientui:", result)
        self.assertIn("This is the content.", result)

    def test_remove_section_between(self):
        text = (
            "Line1\nPacientas:\nJohn Doe\nMore Info\nSveikatos priežiūros įstaigos specialistas:\nDr. Smith\nEnd"
        )
        expected = "Line1\nSveikatos priežiūros įstaigos specialistas:\nDr. Smith\nEnd"
        result = remove_section_between(text, "Pacientas:", "Sveikatos priežiūros įstaigos specialistas:")
        self.assertEqual(result, expected)

    def test_remove_section_between_no_match(self):
        text = "Line1\nSome content\nLine3"
        result = remove_section_between(text, "NonExistentStart:", "NonExistentEnd:")
        self.assertEqual(result, text)  # Should be unchanged

    def test_convert_string_to_history(self):
        input_log = """
        User: Hello, how are you?
        AI: I'm fine, thank you. How can I help you today?
        User: What's the weather like?
        AI: It's sunny and warm today.
        """
        expected = [
            ("Hello, how are you?", "I'm fine, thank you. How can I help you today?"),
            ("What's the weather like?", "It's sunny and warm today.")
        ]
        result = convert_string_to_history(input_log)
        self.assertEqual(result, expected)

    def test_convert_string_to_history_with_missing_ai(self):
        input_log = "User: Hello\nUser: How are you?"
        expected = []  # No AI responses, so nothing to pair
        result = convert_string_to_history(input_log)
        self.assertEqual(result, expected)

    def test_convert_string_to_history_with_extra_whitespace(self):
        input_log = "  User: Hi   \n  AI: Hello!\n"
        expected = [("Hi", "Hello!")]
        result = convert_string_to_history(input_log)
        self.assertEqual(result, expected)


if __name__ == '__main__':
    unittest.main()
