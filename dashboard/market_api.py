"""Read-only opening scenarios and market observations; no jobs or ledger writes."""

import copy
import math
from typing import Protocol

import forward_api as api

fwd, sup = api.fwd, api.sup


class QuoteProvider(Protocol):
    """Replaceable informational feed. Prices are raw BRL, never adjusted.

    Return price, timestamp (timezone required), source and classification:
    realtime_verified, delayed, official_close or unknown. Verified realtime
    also requires realtime_evidence. None price/timestamp means unavailable.
    An adapter must bound/cache external requests; the default makes none.
    """

    def quote(self, ticker, at) -> dict: ...


class OfflineProvider:
    def quote(self, ticker, at):
        return {
            "price": None,
            "timestamp": None,
            "source": "Sem provider intradiário contratado",
            "classification": "unknown",
            "reason": "Cotação intradiária indisponível",
        }


PROVIDER: QuoteProvider = OfflineProvider()


def positive(value):
    return (
        not isinstance(value, bool)
        and isinstance(value, (int, float))
        and math.isfinite(value)
        and value > 0
    )


def frozen(root, session):
    """Verify the already frozen series, never download or repair it."""
    folder = root / "sessions" / api.session_name(session)
    record = api.read(folder / "input.json")
    if not record or record.get("decision_session") != session:
        raise ValueError("missing_frozen_input")
    if fwd.sha_file(folder / "bars.csv") != record["history"]["sha256"]:
        raise ValueError("frozen_bars_hash_mismatch")
    bars = fwd.load_bars(folder)
    if bars.empty or str(bars.index[-1].date()) != session:
        raise ValueError("invalid_frozen_bars")
    return record, bars


def scenario(payload, root=None):
    """Hypothetical evaluation, independent of any actual human approval."""
    root = root or api.OUTPUT
    session = api.session_name(payload["decision_session"])
    digest = payload["decision_sha256"]
    state = api.read(api.supervised_root(root) / "state.json")
    if not state:
        raise ValueError("supervision_not_initialized")
    if not sup.verify(api.supervised_root(root), root, state)["ok"]:
        raise sup.Conflict("supervision_integrity_failed")
    proposal = copy.deepcopy(state["proposals"].get(session))
    if (
        not proposal
        or not isinstance(digest, str)
        or digest != proposal.get("decision_sha256")
    ):
        raise sup.Conflict("decision_hash_mismatch")
    limits = sup.validate_limits(payload["limits"], proposal["direction"])
    price = payload["hypothetical_open"]
    if price is not None and (not positive(price) or not 0.01 <= price <= 1e6):
        raise ValueError("invalid_hypothetical_open")
    band = sup.opening_conditions(proposal, limits, price)
    mark, book = state["mark"], state["portfolio"]
    equity = book["cash"] + book["units"] * mark["close"]
    response = {
        "kind": "hypothetical",
        "persisted": False,
        "decision_session": session,
        "target_session": proposal["target_session"],
        "direction": proposal["direction"],
        "reference": proposal["raw_close"],
        "hypothetical_open": price,
        "gap": price / proposal["raw_close"] - 1
        if price is not None and proposal["raw_close"]
        else None,
        "limits": limits,
        "band": band,
        "current_position": {
            **book,
            "equity": equity,
            "weight": sup.weight(book, mark["close"]),
            "mark": mark,
        },
        "concentration_amount_at_mark": min(
            limits.get("max_concentration", 1), proposal["recommended_target"]
        )
        * equity
        if proposal["recommended_target"] is not None
        else None,
        "allowed": False,
        "estimate": None,
        "target_weight": None,
        "reason": "Informe uma abertura hipotética para calcular a operação.",
        "assumption": "Estimativa na abertura, sem variação posterior: fator ajustado/bruto do último fechamento congelado. Proventos futuros podem alterar esse fator. Não é cotação observada nem execução.",
    }
    if proposal["direction"] not in sup.SIDE or proposal["recommended_target"] is None:
        return {
            **response,
            "reason": "A decisão validada não autoriza uma direção de operação.",
        }
    # A historical decision cannot be transplanted onto a later ledger vintage.
    if mark["session"] != session:
        return {
            **response,
            "reason": "Selecione a decisão correspondente à marca atual da carteira para estimar valores financeiros.",
        }
    proposal["weight_at_close"] = response["current_position"]["weight"]
    effect = sup.effect(proposal, limits)
    response.update(target_weight=effect["target_weight"], pre_open_effect=effect)
    if effect["state"] not in sup.PENDING_EFFECTS:
        return {**response, "reason": effect["reason"]}
    if band["empty"]:
        return {
            **response,
            "reason": "Limites contraditórios: não existe preço positivo na interseção.",
        }
    if price is None:
        return response
    if not positive(proposal["raw_close"]):
        return {**response, "reason": "Fechamento bruto de referência indisponível."}
    try:
        record, bars = frozen(root, session)
        raw_close = (record.get("last_bar_official_raw") or {}).get("fechamento")
        adjusted_close = float(bars.iloc[-1]["fechamento"])
        if (
            not positive(raw_close)
            or not positive(adjusted_close)
            or not positive(mark["close"])
            or not math.isclose(raw_close, proposal["raw_close"], rel_tol=1e-12)
        ):
            raise ValueError("missing_price_base")
    except (ValueError, KeyError, OSError):
        return {
            **response,
            "reason": "Base de preços congelada ausente, incompatível ou sem hash válido; estimativa indisponível.",
        }
    factor = adjusted_close / raw_close
    target = proposal["target_session"]
    if target != str(fwd.target_open(fwd._timestamp(session)).date()):
        raise ValueError("invalid_target_session")
    hypothetical = bars.iloc[-1].copy()
    for key in ("abertura", "fechamento", "maxima", "minima"):
        hypothetical[key] = price * factor
    hypothetical["volume"] = 0.0
    bars = bars.copy()
    bars.loc[fwd._timestamp(target)] = hypothetical
    found = {
        "raw_open": price,
        "raw_gap": response["gap"],
        "adjusted_open": price * factor,
    }
    result, _, dry = sup.evaluate_opening(
        state, proposal, limits, effect["target_weight"], found, bars, target
    )
    response["allowed"] = result["state"] == "EXECUTADA"
    response["reason"] = (
        "Operação permitida neste cenário hipotético; nenhuma ordem criada."
        if response["allowed"]
        else result["reason"]
    )
    if dry is None:
        dry = copy.deepcopy(state)
        dry["pending"] = None
        fwd.reconcile(dry, bars, fwd._timestamp(target))
    if dry:
        after = dry["portfolio"]
        trades = result.get("trades", [])
        value = sum(t["quantity"] * t["price"] for t in trades)
        cost = sum(t["cost"] for t in trades)
        response["estimate"] = {
            "order_value": value,
            "quantity": sum(t["quantity"] for t in trades),
            "cost": cost,
            "cash_after": after["cash"],
            "units_after": after["units"],
            "equity_after": after["cash"] + after["units"] * found["adjusted_open"],
            "concentration_after_costs": sup.weight(after, found["adjusted_open"]),
            "adjusted_open": found["adjusted_open"],
            "adjustment_factor": factor,
            "source": f"sessions/{session}/bars.csv + input.json; abertura hipotética",
        }
        if "max_concentration" in limits:
            response["band"]["checks"].append(
                {
                    "key": "max_concentration",
                    "limit": limits["max_concentration"],
                    "observed": response["estimate"]["concentration_after_costs"],
                    "passed": response["estimate"]["concentration_after_costs"]
                    <= limits["max_concentration"] + 1e-12,
                }
            )
    return response


def session_clock(at):
    """Calendar/clock forecast, never a claim that the exchange is operational."""
    at = fwd.pd.Timestamp(at).tz_convert(fwd.TZ)
    calendar = fwd.B3Calendar()
    today = at.date()
    is_session = bool(calendar.sessions_between(today, today))
    next_day = (
        today
        if is_session and at.time() < fwd.TARGET_OPEN
        else calendar.next_session(today)
    )
    minutes = at.hour * 60 + at.minute
    # ponytail: verified March-October 2026 regular timetable only. Revisit the
    # B3 schedule before expanding; holidays remain the existing B3 calendar.
    known = "2026-03-09" <= str(today) <= "2026-10-30"
    state = "fechada" if not is_session else "desconhecido"
    if is_session and known:
        state = (
            "fechada"
            if minutes < 585
            else "pré-abertura"
            if minutes < 600
            else "negociação"
            if minutes < 1020
            else "encerrada"
        )
    return {
        "state": state,
        "next_session": str(next_day),
        "expected_open": f"{next_day}T10:00:00-03:00"
        if "2026-03-09" <= str(next_day) <= "2026-10-30"
        else None,
        "basis": "Previsão pelo calendário B3 e relógio BRT; pregão regular, sem confirmação de leilão, suspensão ou after-market.",
    }


def observation(provider, at):
    try:
        quote = provider.quote(fwd.TICKER, at)
        if not isinstance(quote, dict):
            raise ValueError("invalid_quote")
        source = quote.get("source")
        classification = quote.get("classification")
        if (
            not isinstance(source, str)
            or not source.strip()
            or classification
            not in (
                "realtime_verified",
                "delayed",
                "official_close",
                "unknown",
            )
        ):
            raise ValueError("invalid_quote_metadata")
        if not positive(quote.get("price")):
            raise ValueError("unavailable")
        timestamp = fwd.pd.Timestamp(quote["timestamp"])
        if timestamp.tzinfo is None or timestamp > at:
            raise ValueError("invalid_quote_timestamp")
        timestamp = timestamp.tz_convert(fwd.TZ)
        if classification == "realtime_verified" and not quote.get("realtime_evidence"):
            classification = "unknown"
        stale = timestamp.date() != at.date() or (at - timestamp).total_seconds() > 1800
        return {
            "price": quote["price"],
            "timestamp": timestamp.isoformat(),
            "source": str(source),
            "classification": classification,
            "stale": stale,
        }
    except (OSError, ValueError, KeyError, TypeError):
        return {
            "price": None,
            "timestamp": None,
            "source": "Provider intradiário indisponível",
            "classification": "unknown",
            "stale": False,
            "reason": "Cotação intradiária indisponível",
        }


def market(root=None, clock=None, provider=None):
    root, at = root or api.OUTPUT, (clock or fwd.now)()
    session = session_clock(at)
    quote = observation(provider or PROVIDER, at)
    supervision = api.supervision(root=root, clock=lambda: at)
    approved = [
        p
        for p in supervision.get("proposals", [])
        if p["order_state"] in api.PENDING
        and (p.get("approval") or {}).get("action") == "APPROVE"
        and not p.get("cancel")
        and not p.get("outcome")
    ]
    monitors = []
    for proposal in approved:
        limits = proposal["approval"]["limits"]
        band = sup.opening_conditions(proposal, limits, quote["price"])
        target_date = proposal["target_session"]
        if not supervision["audit"]["ok"]:
            state = "Dados insuficientes"
        elif at.date().isoformat() < target_date or (
            at.date().isoformat() == target_date and at < sup.stamp(proposal["deadline"])
        ):
            state = "Aguardando abertura"
        elif quote["price"] is None or quote["classification"] in (
            "unknown",
            "official_close",
        ):
            state = "Dados insuficientes"
        elif quote["stale"] or quote["timestamp"][:10] != target_date:
            state = "Informação desatualizada"
        else:
            state = (
                "Fora do limite"
                if any(c["passed"] is False for c in band["checks"])
                else "Dentro do limite"
            )
        if "max_concentration" in limits:
            band["checks"].append(
                {
                    "key": "max_concentration",
                    "limit": limits["max_concentration"],
                    "observed": None,
                    "passed": None,
                }
            )
        monitors.append(
            {
                "decision_session": proposal["decision_session"],
                "target_session": target_date,
                "direction": proposal["direction"],
                "limits": limits,
                "band": band,
                "state": state,
                "reference": proposal["raw_close"],
                "order_state": proposal["order_state"],
                "note": "Comparação informativa de preço observado; não confirma preço de abertura, quantidade, concentração executada ou execução virtual.",
            }
        )
    result = {
        "ticker": fwd.TICKER,
        "as_of": at.isoformat(),
        "session": session,
        "official_close": None,
        "intraday": quote,
        "indicators": None,
        "approved_conditions": monitors,
        "audit": supervision.get("audit"),
        "refresh": "Consulta manual de registros locais; sem polling ou chamadas externas.",
        "execution_authority": "Somente a reconciliação oficial existente registra execução virtual; este painel não escreve no ledger.",
    }
    inputs = sorted((root / "sessions").glob("????-??-??/input.json"))
    if not inputs:
        return {**result, "data_issue": "Sem fechamento oficial congelado."}
    latest = inputs[-1].parent.name
    try:
        record, bars = frozen(root, latest)
        price = (record.get("last_bar_official_raw") or {}).get("fechamento")
        if not positive(price):
            raise ValueError("missing_raw_close")
        result["official_close"] = {
            "price": price,
            "session": latest,
            "timestamp": record.get("fetched_at"),
            "timestamp_basis": "Momento de coleta registrado no input; sessão do fechamento indicada separadamente. Não é horário do último negócio.",
            "source": (record.get("source") or {}).get(
                "raw_ohlcv", "Origem não declarada no input"
            ),
            "classification": "official_close",
            "input_sha256": fwd.sha_file(inputs[-1]),
            "stale": latest != str(fwd.last_closed_session(at).date()),
        }
        from src.indicators import macd, rsi, sma

        close = bars["fechamento"]
        line, signal, _ = macd(close)

        def finite(value):
            return float(value) if math.isfinite(value) else None

        latest_proposal = next(
            (
                p
                for p in supervision.get("proposals", [])
                if p["decision_session"] == latest
            ),
            {},
        )
        result["indicators"] = {
            "sma50": finite(sma(close, 50).iloc[-1]),
            "sma200": finite(sma(close, 200).iloc[-1]),
            "rsi": finite(rsi(close).iloc[-1]),
            "macd": finite(line.iloc[-1]),
            "macd_signal": finite(signal.iloc[-1]),
            "volatility": latest_proposal.get("recent_volatility"),
            "session": latest,
            "source": f"sessions/{latest}/bars.csv SHA256 {record['history']['sha256']}; fechamento ajustado; indicadores locais existentes. Volatilidade: decisão Risk gravada.",
            "classification": "historical",
        }
        result["intraday"]["change_vs_close"] = (
            quote["price"] / price - 1 if quote["price"] is not None else None
        )
    except (ValueError, KeyError, OSError):
        result["data_issue"] = (
            "Fechamento ou série congelada ausente/incompatível; nenhum dado inventado."
        )
    return result
