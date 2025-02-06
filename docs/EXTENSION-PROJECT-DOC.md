## OpenGPTs Model Comparison Module Proof of Concept (POC)

### Project Overview

This Proof of Concept (POC) demonstrates a basic Model Comparison Module for the OpenGPTs project. The module's purpose is to provide a framework for comparing the performance of different Large Language Models (LLMs). This specific POC focuses on comparing Google Gemini and OpenAI GPT-4, but the underlying design can be extended to other LLMs.

**Relation to OpenGPTs**:

OpenGPTs aims to provide an open-source alternative to OpenAI's GPTs and Assistants API. A robust Model Comparison Module would be a valuable addition, enabling users to evaluate and select the most suitable LLM for their specific needs and use cases.

**Specific Use Case**:

This POC addresses a simplified scenario:

1. **File Loading**: The script loads a single text file containing information.
2. **Predefined Questions**: Three predefined questions are asked to both Gemini and GPT-4, prompting them to extract or infer information from the loaded file.
3. **Response Comparison**: The models' responses are compared using two metrics:
    - **ROUGE-1 Score**: Measures the overlap of unigrams (single words) between the models' responses and a predefined "ideal" answer.
    - **Simplified G-Eval**: Assesses the quality of the responses based on basic criteria, providing a holistic evaluation.

Both ROUGE-1 and the simplified G-Eval implementation leverage the `deepeval` library, showcasing its capabilities for automated evaluation of LLMs.

### System Design

**Components**:

The POC consists of the following core components:

- **File Loader**: Loads the content of a single text file.
- **Question Provider**: Holds the three predefined questions.
- **Model Interfaces**: Simple interfaces for interacting with Google Gemini and OpenAI GPT-4.
- **ROUGE-1 Calculator**: Calculates the ROUGE-1 score using `deepeval`.
- **Simplified G-Eval Evaluator**: Implements a basic version of G-Eval using `deepeval`.
- **Result Comparator**: Processes the scores from both metrics and presents the comparison results.

**Data Flow**:

1. The File Loader reads the input text file.
2. The Question Provider supplies the predefined questions to both model interfaces.
3. The Model Interfaces send the questions to Gemini and GPT-4, receiving their respective responses.
4. The ROUGE-1 Calculator and Simplified G-Eval Evaluator compute their scores based on the models' responses and predefined "ideal" answers or evaluation criteria.
5. The Result Comparator compiles the scores, compares them, and presents the final comparison results.

### Key Components Design

**a. File Loading Mechanism**:

- Uses a simple file reader (`with open(...) as f: ...`) to load the entire content of a single text file into memory.

**b. Predefined Questions**:

- Stored as a list of strings within the script. Example:
  ```python
  questions = [
      "What is the main topic of this document?",
      "List three key facts mentioned in the text.",
      "What is the author's opinion on the subject?",
  ]
  ```

**c. Simple Interfaces for Gemini and GPT-4**:

- Basic functions using the respective libraries for interacting with the LLMs. 
  - They send a question and receive the model's response.
  - Authentication and other complexities are handled outside the scope of this POC.

**d. ROUGE-1 Score Calculation using deepeval**:

- Utilizes the `deepeval` library's `rouge_1` function to compute the ROUGE-1 score:
  ```python
  from deepeval.metrics import rouge_1
  rouge_score = rouge_1(model_response, ideal_answer)
  ```

**e. Simplified G-Eval Implementation using deepeval**:

- Implements a streamlined version of G-Eval using `deepeval`.
- **Basic Criteria**: Defined directly within the script as simple rules or checks. Example:
  ```python
  from deepeval.criteria import fact_consistency, relevance, coherence
  criteria = [fact_consistency, relevance, coherence]
  ```
- **Evaluation Process**: The `deepeval` library's `evaluate` function is used to assess the model's response against each criterion.
- **Simplified G-Eval Metric**: A composite score is calculated based on the individual criterion scores, providing an overall quality assessment. Example:
  ```python
  from deepeval.evaluator import Evaluator
  evaluator = Evaluator(criteria)
  g_eval_score = evaluator.evaluate(model_response, input_text)
  ```

**f. Basic Result Comparison Logic**:

- The script compares the ROUGE-1 and simplified G-Eval scores for both Gemini and GPT-4, presenting the comparison in a simple format (e.g., printing to the console).

### Evaluation Metrics

**ROUGE-1 Scoring**:

- `deepeval`'s `rouge_1` function calculates the ROUGE-1 score, which measures the overlap of unigrams (single words) between the model's response and a predefined "ideal" answer. A higher score indicates better agreement between the two.

**Simplified G-Eval Framework**:

- This POC implements a simplified version of G-Eval using `deepeval`. 
  - It defines basic criteria like fact consistency, relevance, and coherence directly within the script.
  - `deepeval`'s `evaluate` function evaluates the model's response against these criteria.
  - A composite score is then calculated by aggregating the individual criterion scores. This simplified metric reflects the overall quality of the response in terms of the defined criteria.

### Implementation Details

- The POC is implemented as a single Python script.
- It leverages several libraries:
  - `langchain` for interacting with LLMs and managing prompts.
  - `deepeval` for automated evaluation metrics.
- Installing `deepeval`:
  ```bash
  pip install deepeval
  ```

### Usage Guide

1. Install the required libraries: `pip install langchain deepeval`
2. Ensure you have valid API keys for accessing both Google Gemini and OpenAI GPT-4.
3. Place your input text file (e.g., `input.txt`) in the same directory as the script.
4. Run the Python script.

**Example Input**:

- A text file containing information.

**Example Output**:

- Console output displaying the ROUGE-1 and simplified G-Eval scores for both Gemini and GPT-4, along with a basic comparison summary.

### Future Expansion

- **Advanced deepeval Features**: Future articles can leverage more sophisticated features of `deepeval`, like:
    - Customizing criteria with specific weights.
    - Implementing more complex G-Eval criteria using the `Criteria` class.
    - Utilizing the `Metric` class for defining and calculating custom metrics beyond ROUGE-1.
- **Expanded Use Cases**: Beyond single file analysis, the module can be extended to:
    - Handle multiple files and datasets.
    - Integrate with OpenGPTs's existing cognitive architectures.
    - Support a wider range of LLMs and evaluation metrics.

This POC lays the foundation for a powerful Model Comparison Module within OpenGPTs, empowering users to make informed decisions about LLM selection by leveraging the capabilities of the `deepeval` library for automated and insightful evaluation.

