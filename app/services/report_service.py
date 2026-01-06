import logging
from io import BytesIO

import pandas as pd
from jinja2 import Environment, FileSystemLoader, select_autoescape
from sqlalchemy.orm import Session
from weasyprint import HTML

# Importaciones de tu proyecto (Manteniendo las originales)
from app.controllers.statistic_controller import StatisticController
from app.schemas.report_schema import ReportFilter, ReportMetadata, ReportType

# Importar el generador de gráficos creado en el paso 1
from app.utils.chart_generator import ChartGenerator

logger = logging.getLogger(__name__)


class ReportService:
    """
    Servicio profesional de reportes con identidad UNL.
    Genera PDF (WeasyPrint), Excel y CSV (Pandas).
    """

    def __init__(self):
        self.statistic_controller = StatisticController()
        # Configuración de Jinja2 para cargar templates HTML
        self.env = Environment(
            loader=FileSystemLoader("app/templates"),
            autoescape=select_autoescape(["html", "xml"]),
        )

    # ========== MÉTODOS PÚBLICOS ==========

    def generate_attendance_report(
        self, db: Session, filters: ReportFilter, user_name: str
    ) -> BytesIO:
        """Genera reporte de asistencia."""
        # 1. Obtener Datos
        stats_data = self.statistic_controller.get_attendance_statistics(
            db=db,
            start_date=filters.start_date,
            end_date=filters.end_date,
            type_athlete=filters.athlete_type.value if filters.athlete_type else None,
            sex=filters.sex.value if filters.sex else None,
            athlete_id=filters.athlete_id,
        )

        metadata = self._build_metadata(
            db, "Reporte de Asistencia", filters, user_name, ReportType.ATTENDANCE
        )

        # 2. Convertir datos crudos a DataFrame para fácil manejo
        df_details = pd.DataFrame(stats_data.get("attendance_by_type", []))

        if filters.format in ["xlsx", "csv"]:
            return self._generate_tabular_report(
                df_details, metadata, filters.format, stats_data
            )

        athlete_info = None

        # 3. Preparar visualización PDF
        # Si es reporte individual (un solo atleta), personalizamos los KPIs
        if filters.athlete_id:
            from app.dao.athlete_dao import AthleteDAO

            athlete_dao = AthleteDAO()
            athlete = athlete_dao.get_by_id(db, filters.athlete_id)

            if athlete:
                athlete_info = {
                    "name": athlete.full_name,
                    "dni": athlete.dni,
                    "category": athlete.type_athlete,
                    "age": athlete.age,
                    "sex": athlete.sex.value
                    if hasattr(athlete.sex, "value")
                    else athlete.sex,
                    "height": athlete.height,
                    "weight": athlete.weight,
                }

            kpi_cards = [
                {
                    "label": "Total Registros",
                    "value": stats_data.get("total_records", 0),
                    "color": "#004C7B",
                },
                {
                    "label": "Presentes",
                    "value": stats_data.get("total_present", 0),
                    "color": "#4F8E3A",
                },
                {
                    "label": "Ausentes",
                    "value": stats_data.get("total_absent", 0),
                    "color": "#BF0811",
                },
                {
                    "label": "Tasa de Asistencia",
                    "value": f"{stats_data.get('overall_attendance_rate', 0):.1f}%",
                    "color": "#211915",
                },
            ]
            chart = (
                None  # No mostramos gráfico de distribución por categoría para uno solo
            )
        else:
            # Reporte grupal
            kpi_cards = [
                {
                    "label": "Total Registros",
                    "value": stats_data.get("total_records", 0),
                    "color": "#004C7B",
                },
                {
                    "label": "Presentes",
                    "value": stats_data.get("total_present", 0),
                    "color": "#4F8E3A",
                },
                {
                    "label": "Tasa Asistencia Global",
                    "value": f"{stats_data.get('overall_attendance_rate', 0):.1f}%",
                    "color": "#BF0811",
                },
            ]
            # Gráfico: Asistencia por Tipo (si hay datos)
            chart = None
            if not df_details.empty:
                chart = ChartGenerator.generate_bar_chart(
                    df_details["type_athlete"].tolist(),
                    df_details["attendance_rate"].tolist(),
                    "Porcentaje de Asistencia por Categoría",
                    y_label="% Asistencia",
                )

        tables = []
        if not df_details.empty:
            tables.append(
                {
                    "title": "Resumen de Asistencia",
                    "headers": [
                        "Categoría",
                        "Total Registros",
                        "Presentes",
                        "% Asistencia",
                    ],
                    "rows": df_details[
                        ["type_athlete", "total", "present", "attendance_rate"]
                    ]
                    .fillna(0)
                    .values.tolist(),
                }
            )

        return self._render_pdf(
            template_name="report_base.html",
            metadata=metadata,
            kpi_cards=kpi_cards,
            main_chart=chart,
            tables=tables,
            athlete_info=athlete_info,
        )

    def generate_tests_report(
        self, db: Session, filters: ReportFilter, user_name: str
    ) -> BytesIO:
        """Genera reporte de evaluaciones y tests."""
        stats_data = self.statistic_controller.get_test_performance(
            db=db,
            start_date=filters.start_date,
            end_date=filters.end_date,
            type_athlete=filters.athlete_type.value if filters.athlete_type else None,
            athlete_id=filters.athlete_id,
        )

        metadata = self._build_metadata(
            db, "Reporte de Rendimiento Físico", filters, user_name, ReportType.TESTS
        )

        df_tests = pd.DataFrame(stats_data.get("tests_by_type", []))

        if filters.format in ["xlsx", "csv"]:
            return self._generate_tabular_report(
                df_tests, metadata, filters.format, stats_data
            )

        athlete_info = None
        if filters.athlete_id:
            from app.dao.athlete_dao import AthleteDAO

            athlete_dao = AthleteDAO()
            athlete = athlete_dao.get_by_id(db, filters.athlete_id)

            if athlete:
                athlete_info = {
                    "name": athlete.full_name,
                    "dni": athlete.dni,
                    "category": athlete.type_athlete,
                    "age": athlete.age,
                    "sex": athlete.sex.value
                    if hasattr(athlete.sex, "value")
                    else athlete.sex,
                    "height": athlete.height,
                    "weight": athlete.weight,
                }

        # KPIs
        total_tests = df_tests["total_tests"].sum() if not df_tests.empty else 0
        avg_score_global = df_tests["avg_score"].mean() if not df_tests.empty else 0

        # Helper para formatear scores y evitar NaN
        def fmt_score(val):
            return f"{val:.2f}" if val is not None and not pd.isna(val) else "-"

        kpi_cards = [
            {
                "label": "Total Tests Ejecutados",
                "value": total_tests,
                "color": "#004C7B",
            },
            {
                "label": "Promedio Global (Pts)",
                "value": fmt_score(avg_score_global) if total_tests > 0 else "-",
                "color": "#4F8E3A",
            },
            {"label": "Tipos de Pruebas", "value": len(df_tests), "color": "#666666"},
        ]

        # Gráfico de Barras: Promedio por Test
        chart = None
        if not df_tests.empty:
            # Filtrar solo tests con avg_score válido para el gráfico
            df_chart = df_tests[df_tests["avg_score"] > 0]

            if not df_chart.empty:
                title_chart = (
                    "Rendimiento Individual por Test"
                    if filters.athlete_id
                    else "Rendimiento Promedio por Tipo de Test"
                )
                chart = ChartGenerator.generate_bar_chart(
                    df_chart["test_type"].tolist(),
                    df_chart["avg_score"].tolist(),
                    title_chart,
                    y_label="Puntaje",
                )

        # Preparar tablas (Manejando N/A visualmente)
        tables = []

        # Tabla 1: Rendimiento por tipo
        if not df_tests.empty:
            # Formatear números para que se vean bien
            formatted_rows = []
            for _, row in df_tests.iterrows():
                formatted_rows.append(
                    [
                        row["test_type"],
                        row["total_tests"],
                        fmt_score(row["avg_score"]),
                        fmt_score(row["min_score"]),
                        fmt_score(row["max_score"]),
                    ]
                )

            tables.append(
                {
                    "title": "Detalle de Rendimiento por Tipo",
                    "headers": [
                        "Tipo de Test",
                        "Total Ejecuciones",
                        "Score Promedio (0-100)",
                        "Mejor Registro",
                        "Peor Registro",
                    ],
                    "rows": formatted_rows,
                }
            )

        # Tabla 2: Top Performers (SOLO SI NO SE FILTRA POR ATLETA)
        if not filters.athlete_id:
            if "top_performers" in stats_data and stats_data["top_performers"]:
                top_df = pd.DataFrame(stats_data["top_performers"])
                tables.append(
                    {
                        "title": "Deportistas con Mayor Actividad",
                        "headers": ["Nombre", "Categoría", "Tests Completados"],
                        "rows": top_df[
                            ["athlete_name", "athlete_type", "tests_completed"]
                        ].values.tolist(),
                    }
                )

        return self._render_pdf(
            template_name="report_base.html",
            metadata=metadata,
            kpi_cards=kpi_cards,
            main_chart=chart,
            tables=tables,
            athlete_info=athlete_info,
        )

    def generate_statistics_report(
        self, db: Session, filters: ReportFilter, user_name: str
    ) -> BytesIO:
        """Genera reporte de estadísticas."""

        athlete_info = None
        chart = None
        tables = []
        kpi_cards = []

        # --- CASO 1: Reporte Individual (Un solo deportista) ---
        if filters.athlete_id:
            metadata = self._build_metadata(
                db,
                "Reporte de Rendimiento Deportivo",
                filters,
                user_name,
                ReportType.STATISTICS,
            )

            from app.dao.athlete_dao import AthleteDAO
            from app.dao.statistic_dao import StatisticDAO

            athlete_dao = AthleteDAO()
            athlete = athlete_dao.get_by_id(db, filters.athlete_id)

            if athlete:
                athlete_info = {
                    "name": athlete.full_name,
                    "dni": athlete.dni,
                    "category": athlete.type_athlete,
                    "age": athlete.age,
                    "sex": athlete.sex.value
                    if hasattr(athlete.sex, "value")
                    else athlete.sex,
                    "height": athlete.height,
                    "weight": athlete.weight,
                }

                # Obtener estadísticas de juego y físicas
                stat_dao = StatisticDAO()
                stats_obj = stat_dao.get_by_field(db, "athlete_id", filters.athlete_id)

                if stats_obj:
                    # KPIs de Juego
                    kpi_cards = [
                        {
                            "label": "Partidos Jugados",
                            "value": stats_obj.matches_played,
                            "color": "#004C7B",
                        },
                        {
                            "label": "Goles",
                            "value": stats_obj.goals,
                            "color": "#4F8E3A",
                        },
                        {
                            "label": "Asistencias",
                            "value": stats_obj.assists,
                            "color": "#211915",
                        },
                        {
                            "label": "Tarjetas (A/R)",
                            "value": f"{stats_obj.yellow_cards}/{stats_obj.red_cards}",
                            "color": "#BF0811",
                        },
                    ]

                    # Tabla de Atributos Físicos
                    tables.append(
                        {
                            "title": "Atributos Físicos (Valoracion 0-100)",
                            "headers": ["Atributo", "Valor", "Estado"],
                            "rows": [
                                [
                                    "Velocidad",
                                    stats_obj.speed
                                    if stats_obj.speed is not None
                                    else "-",
                                    "Registrado" if stats_obj.speed else "Sin datos",
                                ],
                                [
                                    "Resistencia",
                                    stats_obj.stamina
                                    if stats_obj.stamina is not None
                                    else "-",
                                    "Registrado" if stats_obj.stamina else "Sin datos",
                                ],
                                [
                                    "Fuerza",
                                    stats_obj.strength
                                    if stats_obj.strength is not None
                                    else "-",
                                    "Registrado" if stats_obj.strength else "Sin datos",
                                ],
                                [
                                    "Agilidad",
                                    stats_obj.agility
                                    if stats_obj.agility is not None
                                    else "-",
                                    "Registrado" if stats_obj.agility else "Sin datos",
                                ],
                            ],
                        }
                    )

                    # Gráfico Opcional: Goles vs Asistencias (si tiene sentido)
                    if stats_obj.goals > 0 or stats_obj.assists > 0:
                        chart = ChartGenerator.generate_pie_chart(
                            ["Goles", "Asistencias"],
                            [stats_obj.goals, stats_obj.assists],
                            "Contribución Ofensiva",
                        )
                else:
                    kpi_cards = [
                        {
                            "label": "Info",
                            "value": "Sin Estadísticas",
                            "color": "#666666",
                        }
                    ]

        # --- CASO 2: Reporte del Club (General) ---
        else:
            stats_data = self.statistic_controller.get_club_overview(
                db=db,
                type_athlete=filters.athlete_type.value
                if filters.athlete_type
                else None,
                sex=filters.sex.value if filters.sex else None,
            )

            metadata = self._build_metadata(
                db,
                "Reporte de Estadísticas del Club",
                filters,
                user_name,
                ReportType.STATISTICS,
            )

            kpi_cards = [
                {
                    "label": "Total Deportistas",
                    "value": stats_data.get("total_athletes", 0),
                    "color": "#BF0811",
                },
                {
                    "label": "Activos",
                    "value": stats_data.get("active_athletes", 0),
                    "color": "#4F8E3A",
                },
                {
                    "label": "Total Evaluaciones",
                    "value": stats_data.get("total_tests_conducted", 0),
                    "color": "#004C7B",
                },
            ]

            # Gráfico: Distribución por Género
            gender_dist = stats_data.get("gender_distribution", {})
            if gender_dist:
                labels = list(gender_dist.keys())
                values = list(gender_dist.values())
                chart = ChartGenerator.generate_pie_chart(
                    labels, values, "Distribución por Género"
                )

            # df_overview = pd.DataFrame(
            #     list(stats_data.items()), columns=["Métrica", "Valor"]
            # )

            # Tabla resumen (filtrando cosas que no son dicts)
            clean_rows = []
            for k, v in stats_data.items():
                if isinstance(v, (int, float, str)):
                    clean_rows.append([k.replace("_", " ").title(), v])

            if clean_rows:
                tables.append(
                    {
                        "title": "Resumen General",
                        "headers": ["Métrica", "Valor"],
                        "rows": clean_rows,
                    }
                )

        if filters.format in ["xlsx", "csv"]:
            # Para exportar, creamos un DF con todas las métricas principales
            # y pasamos stats_data como extra_data para las hojas adicionales
            if filters.athlete_id and athlete_info and kpi_cards:
                # Reporte individual: incluir info del atleta y KPIs
                export_rows = [["Deportista", athlete_info.get("name", "")]]
                export_rows.append(["DNI", athlete_info.get("dni", "")])
                export_rows.append(["Categoría", athlete_info.get("category", "")])
                export_rows.append(["Edad", athlete_info.get("age", "")])
                export_rows.append(["Sexo", athlete_info.get("sex", "")])
                export_rows.append(["", ""])  # Separador
                for kpi in kpi_cards:
                    export_rows.append([kpi["label"], kpi["value"]])
                df_export = pd.DataFrame(export_rows, columns=["Campo", "Valor"])
                return self._generate_tabular_report(
                    df_export, metadata, filters.format
                )
            else:
                # Reporte del club: usar stats_data existente
                df_export = pd.DataFrame(kpi_cards)
                return self._generate_tabular_report(
                    df_export, metadata, filters.format, stats_data
                )

        return self._render_pdf(
            template_name="report_base.html",
            metadata=metadata,
            kpi_cards=kpi_cards,
            main_chart=chart,
            tables=tables,
            athlete_info=athlete_info,
        )

    # ========== MÉTODOS PRIVADOS (Helpers) ==========

    def _render_pdf(
        self,
        template_name: str,
        metadata: ReportMetadata,
        kpi_cards: list,
        main_chart: str,
        tables: list,
        athlete_info: dict = None,
    ) -> BytesIO:
        """Renderiza HTML y lo convierte a PDF usando WeasyPrint."""
        template = self.env.get_template(template_name)

        html_string = template.render(
            title=metadata.title,
            metadata=metadata,
            kpi_cards=kpi_cards,
            main_chart=main_chart,
            tables=tables,
            athlete_info=athlete_info,
        )

        buffer = BytesIO()
        # Generar PDF
        HTML(string=html_string).write_pdf(buffer)
        buffer.seek(0)
        return buffer

    def _generate_tabular_report(
        self,
        df: pd.DataFrame,
        metadata: ReportMetadata,
        fmt: str,
        extra_data: dict = None,
    ) -> BytesIO:
        """Genera Excel o CSV usando Pandas con todos los datos relevantes."""
        buffer = BytesIO()

        if fmt == "csv":
            # Para CSV, exportar el DataFrame principal
            df.to_csv(buffer, index=False, encoding="utf-8-sig")

        elif fmt == "xlsx":
            with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
                # Hoja 1: Información / Metadata
                info_rows = [
                    ["Reporte", metadata.title],
                    ["Generado Por", metadata.generated_by],
                    ["Fecha", metadata.generated_at.strftime("%d/%m/%Y %H:%M")],
                    ["Período", metadata.period or "Todo el histórico"],
                ]
                # Añadir filtros aplicados
                if metadata.filters_applied:
                    for k, v in metadata.filters_applied.items():
                        info_rows.append([f"Filtro: {k}", v])

                pd.DataFrame(info_rows, columns=["Campo", "Valor"]).to_excel(
                    writer, sheet_name="Información", index=False
                )

                # Hoja 2: Resumen (KPIs y estadísticas principales)
                if extra_data:
                    summary_rows = []
                    # Extraer datos de resumen del extra_data
                    if "total_records" in extra_data:
                        summary_rows.append(
                            ["Total Registros", extra_data.get("total_records", 0)]
                        )
                    if "total_present" in extra_data:
                        summary_rows.append(
                            ["Presentes", extra_data.get("total_present", 0)]
                        )
                    if "total_absent" in extra_data:
                        summary_rows.append(
                            ["Ausentes", extra_data.get("total_absent", 0)]
                        )
                    if "overall_attendance_rate" in extra_data:
                        summary_rows.append(
                            [
                                "Tasa de Asistencia (%)",
                                f"{extra_data.get('overall_attendance_rate', 0):.1f}%",
                            ]
                        )
                    if "total_tests" in extra_data:
                        summary_rows.append(
                            ["Total Tests", extra_data.get("total_tests", 0)]
                        )
                    if "total_athletes" in extra_data:
                        summary_rows.append(
                            ["Total Deportistas", extra_data.get("total_athletes", 0)]
                        )
                    if "active_athletes" in extra_data:
                        summary_rows.append(
                            [
                                "Deportistas Activos",
                                extra_data.get("active_athletes", 0),
                            ]
                        )
                    if "inactive_athletes" in extra_data:
                        summary_rows.append(
                            [
                                "Deportistas Inactivos",
                                extra_data.get("inactive_athletes", 0),
                            ]
                        )
                    if "total_evaluations" in extra_data:
                        summary_rows.append(
                            [
                                "Total Evaluaciones",
                                extra_data.get("total_evaluations", 0),
                            ]
                        )

                    if summary_rows:
                        pd.DataFrame(
                            summary_rows, columns=["Métrica", "Valor"]
                        ).to_excel(writer, sheet_name="Resumen", index=False)

                    # Hoja adicional: Distribución por tipo si existe
                    if (
                        "attendance_by_type" in extra_data
                        and extra_data["attendance_by_type"]
                    ):
                        df_by_type = pd.DataFrame(extra_data["attendance_by_type"])
                        if not df_by_type.empty:
                            # Renombrar columnas para mejor lectura
                            df_by_type.columns = [
                                col.replace("_", " ").title()
                                for col in df_by_type.columns
                            ]
                            df_by_type.to_excel(
                                writer,
                                sheet_name="Por Categoría",
                                index=False,
                            )

                    # Hoja adicional: Distribución por atleta tipo
                    if (
                        "athletes_by_type" in extra_data
                        and extra_data["athletes_by_type"]
                    ):
                        df_athletes = pd.DataFrame(extra_data["athletes_by_type"])
                        if not df_athletes.empty:
                            df_athletes.columns = [
                                col.replace("_", " ").title()
                                for col in df_athletes.columns
                            ]
                            df_athletes.to_excel(
                                writer,
                                sheet_name="Deportistas por Tipo",
                                index=False,
                            )

                    # Hoja adicional: Distribución por género
                    if (
                        "athletes_by_gender" in extra_data
                        and extra_data["athletes_by_gender"]
                    ):
                        df_gender = pd.DataFrame(extra_data["athletes_by_gender"])
                        if not df_gender.empty:
                            df_gender.columns = [
                                col.replace("_", " ").title()
                                for col in df_gender.columns
                            ]
                            df_gender.to_excel(
                                writer,
                                sheet_name="Deportistas por Género",
                                index=False,
                            )

                    # Hoja adicional: Tests por tipo
                    if "tests_by_type" in extra_data and extra_data["tests_by_type"]:
                        df_tests = pd.DataFrame(extra_data["tests_by_type"])
                        if not df_tests.empty:
                            df_tests.columns = [
                                col.replace("_", " ").title()
                                for col in df_tests.columns
                            ]
                            df_tests.to_excel(
                                writer,
                                sheet_name="Tests por Tipo",
                                index=False,
                            )

                    # Hoja adicional: Top performers
                    if "top_performers" in extra_data and extra_data["top_performers"]:
                        df_top = pd.DataFrame(extra_data["top_performers"])
                        if not df_top.empty:
                            df_top.columns = [
                                col.replace("_", " ").title() for col in df_top.columns
                            ]
                            df_top.to_excel(
                                writer,
                                sheet_name="Mejores Deportistas",
                                index=False,
                            )

                    # Hoja adicional: Asistencia por período
                    if (
                        "attendance_by_period" in extra_data
                        and extra_data["attendance_by_period"]
                    ):
                        df_period = pd.DataFrame(extra_data["attendance_by_period"])
                        if not df_period.empty:
                            df_period.columns = [
                                col.replace("_", " ").title()
                                for col in df_period.columns
                            ]
                            df_period.to_excel(
                                writer,
                                sheet_name="Asistencia por Fecha",
                                index=False,
                            )

                # Hoja final: Datos Detallados (el DataFrame principal)
                if not df.empty:
                    # Renombrar columnas para mejor lectura
                    df_export = df.copy()
                    df_export.columns = [
                        col.replace("_", " ").title() for col in df_export.columns
                    ]
                    df_export.to_excel(
                        writer, sheet_name="Datos Detallados", index=False
                    )

        buffer.seek(0)
        return buffer

    def _build_metadata(
        self,
        db: Session,
        title: str,
        filters: ReportFilter,
        user_name: str,
        report_type: ReportType,
    ) -> ReportMetadata:
        """Construye el objeto de metadatos (Lógica original preservada)."""
        period = "Histórico Completo"
        if filters.start_date and filters.end_date:
            if (
                filters.start_date.month == filters.end_date.month
                and filters.start_date.year == filters.end_date.year
            ):
                period = filters.start_date.strftime("%B %Y")
            else:
                start_str = filters.start_date.strftime("%d/%m/%Y")
                end_str = filters.end_date.strftime("%d/%m/%Y")
                period = f"{start_str} - {end_str}"

        filters_dict = {}
        if filters.athlete_id:
            # Si ya obtuvimos la info del atleta en el método principal, aquí
            # podemos dejar que el template maneje la visualización completa.
            # Sin embargo, para mantener coherencia en el metadata box:
            from app.dao.athlete_dao import AthleteDAO

            athlete_dao = AthleteDAO()
            try:
                athlete = athlete_dao.get_by_id(db, filters.athlete_id)
                filters_dict["Deportista"] = athlete.full_name if athlete else ""
            except Exception:
                pass  # Si falla, simplemente no mostramos nada y dejamos que athlete

        if filters.athlete_type:
            filters_dict["Categoría"] = filters.athlete_type.value
        if filters.sex:
            filters_dict["Sexo"] = filters.sex.value

        return ReportMetadata(
            title=title,
            generated_by=user_name,
            filters_applied=filters_dict,
            period=period,
        )
