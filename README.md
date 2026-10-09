# GitHub Codespaces ♥️ Jupyter Notebooks

Welcome to your shiny new codespace! We've got everything fired up and running for you to explore Python and Jupyter notebooks.

You've got a blank canvas to work on from a git perspective as well. There's a single initial commit with what you're seeing right now - where you go from here is up to you!

Everything you do here is contained within this one codespace. There is no repository on GitHub yet. If and when you’re ready you can click "Publish Branch" and we’ll create your repository and push up your project. If you were just exploring then and have no further need for this code then you can simply delete your codespace and it's gone forever.

## Run the CIF & FOC calculator

The calculator is a Streamlit app. Run it as a Python script from the Codespaces
terminal, not as a notebook cell:

```bash
./.venv/bin/pip install -r requirements.txt
./.venv/bin/streamlit run cif_foc_app.py
```

Open the forwarded port shown by Streamlit (usually **8501**; it may choose
another port if 8501 is already in use). Running Streamlit code directly inside
the Jupyter kernel does not start a Streamlit server and can cause the kernel
to be mistaken for the app.
