"""Execute the distribution-only notebook with this Python interpreter."""
from pathlib import Path
import sys
import nbformat
from nbclient import NotebookClient
from jupyter_client import KernelManager
from jupyter_client.kernelspec import KernelSpec

here = Path(__file__).resolve().parent
path = here / "pt_distribution_diagnostics.ipynb"
notebook = nbformat.read(path, as_version=4)
manager = KernelManager(kernel_name="python3")
# Use the invoking analysis environment, regardless of global Jupyter kernels.
manager._kernel_spec = KernelSpec(
    argv=[sys.executable, "-m", "ipykernel_launcher", "-f", "{connection_file}"],
    display_name="Analysis Python", language="python")
client = NotebookClient(notebook, km=manager, timeout=900,
                        resources={"metadata": {"path": str(here)}})
try:
    client.execute(cleanup_kc=True)
finally:
    nbformat.write(notebook, path)
print(f"Executed {path}")
