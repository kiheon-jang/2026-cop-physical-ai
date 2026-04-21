url : https://huggingface.co/docs/lerobot/installation


```
conda deactivate
conda remove -n lerobot --all -y
conda create -n lerobot python=3.12 -y
conda activate lerobot
conda install -c conda-forge ffmpeg git-lfs -y
git lfs install
cd ~
rm -rf lerobot
git clone https://github.com/huggingface/lerobot.git
cd lerobot
python -m pip install -U pip
python -m pip install -e ".[feetech]"
python -c "import sys, lerobot; print(sys.version); print(lerobot.__version__); print(lerobot.__file__)"
```

---


```
wget "https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-$(uname)-$(uname -m).sh"
bash Miniforge3-$(uname)-$(uname -m).sh
```


```
conda create -y -n lerobot python=3.10
```


```
conda activate lerobot
```


```
conda install ffmpeg -c conda-forge
```


```
git clone https://github.com/huggingface/lerobot.git
cd lerobot
```

```
pip install -e .
```

우린 feetech 모터를 샀음
```
pip install lerobot
pip install -e ".[aloha]" # Specific features (Aloha)
pip install 'lerobot[feetech]'      # Feetech motor support
```


