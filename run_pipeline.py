from src.db.connection import SessionLocal, engine, get_session
from src.db.models import Ativo, Base, CotacaoDiaria, IndicadorTecnico
from src.pipeline.extract import DataExtractor
from src.pipeline.load import DataLoader
from src.pipeline.transform import DataTransformer

Base.metadata.create_all(engine)

print("Baixando PETR4.SA...")
extractor = DataExtractor()
df = extractor.download("PETR4.SA", "2024-01-01", "2024-12-31")
print(f"Extraido: {len(df)} linhas")

transformer = DataTransformer()
df_clean = transformer.clean(df)
df_all = transformer.calculate_indicators(df_clean)
print(f"Transformado: {len(df_all)} linhas")

loader = DataLoader(get_session)
loader.upsert_cotacoes("PETR4.SA", df_all)
loader.batch_insert_indicators("PETR4.SA", df_all)
print("Carregado!")

session = SessionLocal()
print(f"Ativos: {session.query(Ativo).count()}")
print(f"Cotacoes: {session.query(CotacaoDiaria).count()}")
print(f"Indicadores: {session.query(IndicadorTecnico).count()}")
session.close()
