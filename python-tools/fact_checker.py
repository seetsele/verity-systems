"""
Verity Systems - Simple Fact Checker
"""

import anthropic
import os
from dotenv import load_dotenv

load_dotenv()
def check_facts(content):
    """
    Simple fact-checking function
    """
    print("\n🎯 VERITY FACT CHECKER")
    print("=" * 60)
    api_key = os.getenv('ANTHROPIC_API_KEY')
    client = anthropic.Anthropic(api_key=api_key)
    print("🔍 Analyzing content...")
    response = client.completions.create(
        model="claude-2",
        max_tokens_to_sample=2000,
        temperature=0,
        prompt=f"""\
        You are Verity, a fact-checking AI assistant. Your task is to analyze the following content and identify any factual inaccuracies. Provide a summary of your findings.

        Content:
        {content}

        Instructions:
        1. Identify any statements that are factually incorrect.
        2. Provide evidence or sources to support your findings.
        3. Summarize your conclusions clearly.
        4. What claims can be verified?
        5. Are any claims likely false or misleading?
        6. What should be checked?

        Begin your analysis below:
        """
    )
    print("\n📄 RESULTS:")
    print("=" * 60)
    print(response.content[0].text)
    print("=" * 60)
    print("\n✓ Analysis complete!\n")


if __name__ == "__main__":
    test_content = """\
    The University of Botswana was founded in 1982 and has 50,000 students.
    It is ranked #1 in Africa and has partnerships with Harvard.
    """
    check_facts(test_content)




