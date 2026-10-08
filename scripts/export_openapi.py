import json
import sys
from pathlib import Path

# Agregar raíz del proyecto al path
root_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root_dir))

from api.main import app  # noqa: E402


def export_openapi(output_path: str = "openapi.json"):
    """Exporta el esquema OpenAPI completo de FastAPI en formato JSON."""
    schema = app.openapi()
    target = root_dir / output_path
    with open(target, "w", encoding="utf-8") as f:
        json.dump(schema, f, indent=2, ensure_ascii=False)
    print(f"[OK] Esquema OpenAPI exportado exitosamente a: {target}")

if __name__ == "__main__":
    export_openapi()
