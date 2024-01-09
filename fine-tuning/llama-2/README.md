# Quantized Low-Rank Adaptation (QLoRA) Fine-Tuning for Structured Responses

Why?
    - Models with billions of parameters require very large GPU clusters to run.
    - Fine-tuning is expensive, especially for large models, since all model parameters are updated.
    - We use quantization to compress the model such that it loads into a single GPUs memory, then only update the most important weights during fine-tuning.

Definitions:
    Quantization - A way to discretize the continuous values into a finite set of values. Practically this means representing large floating point numbers with a smaller set of integers, thus compressing, for example, a 32-bit model into a 4-bit representation. Quantization is done to run models on smaller/cheaper hardware, at the expense of model performance.
    PEFT: Parameter Efficient Fine-Tuning - Only some of the weights are updated during fine-tuning, examples include LoRA, QLoRA, 
    LoRA: Low-Rank Adaptation - A specific PEFT technique, wherebhy we only update the low-rank weights, which are the most important anyway.
    QLoRA: Quantized LoRA - Quantizing the weight matrices in 4-bit integers, then applying LoRA.
    