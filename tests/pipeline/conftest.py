"""Conftest para testes de pipeline — mocka o módulo prefect.

O prefect 2.x tem múltiplas cadeias de import quebradas (ex: módulos
que importam classes que não existem mais em prefect.exceptions ou
prefect.client.base). Em vez de depender de uma versão funcional do
prefect, substituímos o módulo por um mock que expõe apenas os
decorators ``flow`` e ``task`` que o módulo ``src.pipeline.flows``
precisa.
"""

import sys
import unittest.mock


def _install_prefect_mock() -> None:
    """Instala um mock do módulo ``prefect`` em ``sys.modules``.

    Os decorators mockados são pass-through identities, o que permite
    que os testes de unidade do flow executem as funções normalmente.
    """
    if "prefect" in sys.modules:
        return  # já mockado ou carregado

    mock_prefect = unittest.mock.MagicMock()

    # flow e task como pass-through decorators
    def passthrough_decorator(fn=None, **kwargs):
        if fn is not None:
            return fn
        return passthrough_decorator

    mock_prefect.flow = passthrough_decorator
    mock_prefect.task = passthrough_decorator

    sys.modules["prefect"] = mock_prefect


_install_prefect_mock()
