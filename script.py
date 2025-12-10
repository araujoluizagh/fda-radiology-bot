import requests
import csv
from datetime import datetime, timedelta

# Arquivo CSV de saída
OUTPUT_FILE = "radiology_510k.csv"

# Endpoint da API openFDA 510(k)
BASE_URL = "https://api.fda.gov/device/510k.json"


def fetch_radiology_510k(days_back=1, max_records=1000):
    """
    Busca registros de 510(k) relacionados a Radiology
    em uma janela de dias para trás, usando openFDA.
    Se a API der erro (ex.: 500), tratamos e retornamos lista vazia
    para não quebrar o workflow.
    """
    # Em vez de usar "hoje", vamos usar ATÉ ONTEM,
    # porque hoje pode ainda não ter dados e às vezes causa erro.
    today_utc = datetime.utcnow().date()
    end_date = today_utc - timedelta(days=1)            # ontem
    start_date = end_date - timedelta(days=days_back-1) # janela para trás

    end_str = end_date.strftime("%Y%m%d")
    start_str = start_date.strftime("%Y%m%d")

    query = (
        f"advisory_committee:radiology+"
        f"decision_date:[{start_str}+TO+{end_str}]"
    )

    params = {
        "search": query,
        "limit": max_records,
    }

    print(f"Buscando dados de {start_str} até {end_str}...")

    try:
        r = requests.get(BASE_URL, params=params, timeout=30)
        r.raise_for_status()
        data = r.json()
    except requests.HTTPError as e:
        # Se a API do FDA estiver instável, não derruba o workflow
        print(f"HTTPError ao chamar openFDA: {e}")
        return []
    except Exception as e:
        # Qualquer outro erro de rede/parse
        print(f"Erro geral ao chamar openFDA: {e}")
        return []

    results = data.get("results", [])
    print(f"Encontrados {len(results)} registros.")
    return results


def save_to_csv(records, filename=OUTPUT_FILE):
    """
    Salva os registros em um CSV simples.
    """
    fieldnames = [
        "k_number",
        "applicant",
        "device_name",
        "decision_date",
        "advisory_committee",
        "decision_code",
    ]

    with open(filename, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for rec in records:
            writer.writerow({
                "k_number": rec.get("k_number"),
                "applicant": rec.get("applicant"),
                "device_name": rec.get("device_name"),
                "decision_date": rec.get("decision_date"),
                "advisory_committee": rec.get("advisory_committee"),
                "decision_code": rec.get("decision_code"),
            })

    print(f"CSV salvo em: {filename}")


def main():
    # 1 dia para trás = ontem apenas
    records = fetch_radiology_510k(days_back=1, max_records=1000)
    # Mesmo se vier lista vazia, ainda salvamos um CSV com cabeçalho
    save_to_csv(records, OUTPUT_FILE)


if __name__ == "__main__":
    main()
