import os
import io
from contextlib import redirect_stdout
import pytest
from pysao.parse_xpahtml import parse_xpa_help
from pysao.ds9_xpa_help import ds9_help

def test_parse_xpa_help():
    # Load the actual doc/xpa.html file
    xpa_html_path = os.path.join(os.path.dirname(__file__), "..", "doc", "xpa.html")
    with open(xpa_html_path, "r", encoding="iso-8859-1") as f:
        html_content = f.read()
    
    help_data = parse_xpa_help(html_content)
    
    assert isinstance(help_data, dict)
    assert len(help_data) > 0
    
    # Test a specific command: 2mass
    assert "2mass" in help_data
    assert "2MASS" in help_data["2mass"]["expl"]
    assert "syntax" in help_data["2mass"]
    assert "example" in help_data["2mass"]
    
    # Test 'about'
    assert "about" in help_data
    assert "credits" in help_data["about"]["expl"].lower()
    
    # Verify that tags like <br> are handled (converted to newlines or spaces)
    # Our new parser handles <br> by writing \n
    assert "\n" in help_data["2mass"]["syntax"] or " " in help_data["2mass"]["syntax"]

def test_ds9_help_summary():
    # Test the ds9_help class wrapper
    xpa_html_path = os.path.join(os.path.dirname(__file__), "..", "doc", "xpa.html")
    with open(xpa_html_path, "r", encoding="iso-8859-1") as f:
        html_content = f.read()
    
    h = ds9_help(html_content)
    
    # Test __call__ without arguments (summary)
    f = io.StringIO()
    with redirect_stdout(f):
        h()
    
    output = f.getvalue()
    assert "[2mass]" in output
    assert "[about]" in output
    assert "[analysis]" in output

def test_ds9_help_command():
    xpa_html_path = os.path.join(os.path.dirname(__file__), "..", "doc", "xpa.html")
    with open(xpa_html_path, "r", encoding="iso-8859-1") as f:
        html_content = f.read()
    
    h = ds9_help(html_content)
    
    # Test specific command help
    f = io.StringIO()
    with redirect_stdout(f):
        h("about")
    
    output = f.getvalue()
    assert "credits" in output.lower()
    assert "<Syntax>" in output
    assert "<Example>" in output

def test_ds9_help_invalid_command():
    xpa_html_path = os.path.join(os.path.dirname(__file__), "..", "doc", "xpa.html")
    with open(xpa_html_path, "r", encoding="iso-8859-1") as f:
        html_content = f.read()
    
    h = ds9_help(html_content)
    
    from pysao.ds9_xpa_help import Invalid_Ds9_Xpa_command
    with pytest.raises(Invalid_Ds9_Xpa_command):
        h("non_existent_command_xyz")