#!/bin/bash
cd /home/sibayan_mitra_2024/neel/value-leakage-forensics
echo "=== installing torch 2.11.0+cu128 (driver 570 / CUDA 12.8 compatible) ==="
.venv/bin/pip install --no-cache-dir \
  torch==2.11.0 torchaudio==2.11.0 torchvision \
  --index-url https://download.pytorch.org/whl/cu128 2>&1 | tail -20
echo "=== installing vllm 0.26.0 (pins torch 2.11.0) ==="
.venv/bin/pip install --no-cache-dir vllm==0.26.0 2>&1 | tail -20
echo "=== verify ==="
.venv/bin/python -c "import torch,vllm; print('TORCH',torch.__version__,'CUDA_OK',torch.cuda.is_available(),'VLLM',vllm.__version__)"
