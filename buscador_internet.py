#!/usr/bin/env python3
"""Busca informações na internet usando a API Instant Answer do DuckDuckGo."""

from __future__ import annotations

import argparse
import json
import sys
import textwrap
from dataclasses import dataclass
from typing import Iterable
from urllib.error import HTTPError, URLError
from urllib.parse import quote_plus
from urllib.request import urlopen

API_URL = "https://api.duckduckgo.com/?q={query}&format=json&no_html=1&skip_disambig=1"


@dataclass
class ResultadoBusca:
    titulo: str
    descricao: str
    link: str


def buscar_informacoes(termo: str, limite: int = 5) -> tuple[str, list[ResultadoBusca]]:
    """Busca um termo na web e retorna um resumo principal + resultados relacionados."""
    url = API_URL.format(query=quote_plus(termo))

    with urlopen(url, timeout=10) as resposta:
        dados = json.loads(resposta.read().decode("utf-8"))

    resumo = dados.get("AbstractText", "") or "Nenhum resumo direto encontrado."
    relacionados = list(_extrair_relacionados(dados.get("RelatedTopics", []), limite))
    return resumo, relacionados


def _extrair_relacionados(topicos: list[dict], limite: int) -> Iterable[ResultadoBusca]:
    """Extrai itens relacionados da resposta da API."""
    resultados: list[ResultadoBusca] = []

    def adicionar_item(item: dict) -> None:
        texto = item.get("Text", "")
        link = item.get("FirstURL", "")
        if not texto or not link:
            return
        titulo = texto.split(" - ", maxsplit=1)[0].strip()
        resultados.append(ResultadoBusca(titulo=titulo, descricao=texto, link=link))

    for topico in topicos:
        if len(resultados) >= limite:
            break

        if "Topics" in topico:
            for subtopico in topico["Topics"]:
                if len(resultados) >= limite:
                    break
                adicionar_item(subtopico)
        else:
            adicionar_item(topico)

    return resultados[:limite]


def criar_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Busca informações na internet usando DuckDuckGo."
    )
    parser.add_argument("termo", help="Termo que será pesquisado na internet")
    parser.add_argument(
        "--limite",
        type=int,
        default=5,
        help="Quantidade máxima de resultados relacionados (padrão: 5)",
    )
    return parser


def main() -> int:
    parser = criar_parser()
    args = parser.parse_args()

    if args.limite <= 0:
        print("Erro: o limite precisa ser maior que zero.", file=sys.stderr)
        return 2

    try:
        resumo, relacionados = buscar_informacoes(args.termo, args.limite)
    except (HTTPError, URLError, TimeoutError) as erro:
        print(f"Falha ao buscar dados na internet: {erro}", file=sys.stderr)
        return 1

    print(f"\n🔎 Resultado para: {args.termo}\n")
    print("Resumo principal:")
    print(textwrap.fill(resumo, width=90))

    if relacionados:
        print("\nResultados relacionados:")
        for indice, item in enumerate(relacionados, start=1):
            print(f"{indice}. {item.titulo}")
            print(f"   {item.descricao}")
            print(f"   {item.link}")
    else:
        print("\nNenhum resultado relacionado encontrado.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
