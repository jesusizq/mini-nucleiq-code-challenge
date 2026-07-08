# CellsIA's Code Challenge

In the real world, a tissue sample (for example from a biopsy of a breast tumour) is prepared in the lab, sliced into very thin sections, stained, and photographed at very high resolution. The resulting digital image is called a whole-slide image, or WSI. Pathologists review these images to look for clinically relevant biological markers, such as proteins, receptors, proliferation markers, or staining patterns.

NucleIQ is a digital pathology platform that uses AI/ML models to help detect and quantify those markers in tissue samples, reducing the manual review burden and helping pathologists focus their attention on the most relevant findings.

For this challenge, we reduce that idea to a toy model: a sample is just an array of 0s and 1s, and each “algorithm” is a simple rule that detects a different pattern in that array.

---

We’re interested to see how you work and not so much in the specific framework, language, or delivery mechanism you choose. 

You can implement the solution as anything that makes sense to you (don’t get obsessed with implementing a CLI, a simple app, or an HTTP API). We prefer simple code with good tests over a larger or more polished application with unclear design.

We want to see hoy YOU code and understand how YOU think and solve problems, not an LLM.

For guidance, the solution should take around 2–3 hours to implement.

## Instructions

Fork this repository and once completed, send us the url of your repository back.

Please don’t squash your commits before submitting; we want to see the progression of your work, not only the final result.

Include a short README explaining how to run the tests, the solution, and any assumptions or trade-offs you made.

## The task

Write some code (mini-nucleiq) that allows pathologists to analyze breast tissue samples and detect simplified marker patterns associated with breast cancer screening using one or more algorithms. Each sample contains a simplified representation of cells (an array of 0s and 1s). The pathologist should be able to:

1. Submit a sample for analysis
    * Specify the sample name and one or more algorithms to analyze the sample with
    * Retrieve the sample data by issuing a request to the Samples API specified below
2. See the result of the analysis
    * Result of each selected algorithm (with number of positive cells detected and positivity percentage)
    * Final sample result (POSITIVE when more than half of the selected algorithms are positive; otherwise NEGATIVE)

The pathologists can use one or more algorithms (described below); each one detects a different simplified marker pattern in the sample. 

## Algorithms

Each algorithm detects a different simplified marker pattern in the sample. The algorithms are intentionally simple (no ML or AI needed) and all indexes start at 0.

**even-zeroes**: counts each 0 at an even index as a positive cell; the algorithm is positive when positive cells are more than 30% of all cells.

**contiguous-ones**: counts each 1 that is next (but not previous) to another 1 as a positive cell;  the algorithm is positive when positive cells are more than 20% of all cells.

**surrounded-ones**: counts each 1 whose previous and next cells are both 0 as a positive cell; the algorithm is positive when positive cells are more than 10% of all cells.

## Samples API

The sample API is an existing API that returns details for a sample, identified by it’s name. mini-nucleiq should integrate with the samples API to retrieve sample tissue data (cells).

Base URL: `https://raw.githubusercontent.com/cellsia/mini-nucleiq-code-challenge/main/`

View Sample: `GET /mini-nucleiq-code-challenge/samples/{sample}.json`

List of available samples * _sample-a_ * _sample-b_ * _sample-c_ * _sample-d_ * _sample-e_

## Example

The example below can be used to confirm your calculations.

### Inputs

Analyze sample-c with: even-zeroes, contiguous-ones, surrounded-ones

### Results

even-zeroes: Positive cells = 3, positivity = 30%, result = NEGATIVE

contiguous-ones: positive cells = 2, positivity = 20%, result = NEGATIVE

surrounded-ones: positive cells = 2, positivity = 20% result = POSITIVE

Final sample result: POSITIVE
