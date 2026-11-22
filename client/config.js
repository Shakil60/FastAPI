// URL de l'API appelée par le client.
// En local (client servi sur localhost), on vise l'API lancée avec uvicorn ;
// en ligne, on vise l'application API déployée sur Scalingo.
window.API_URL = ["localhost", "127.0.0.1"].includes(window.location.hostname)
  ? "http://localhost:8000"
  : "https://fastapi.osc-fr1.scalingo.io";
