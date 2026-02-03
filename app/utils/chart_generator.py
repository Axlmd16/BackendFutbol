import base64
import io

import matplotlib.pyplot as plt


class ChartGenerator:
    # Colores corporativos UNL
    COLORS = {
        "red": "#BF0811",
        "green": "#4F8E3A",
        "black": "#211915",
        "blue": "#004C7B",
    }

    @staticmethod
    def _to_base64(fig):
        img = io.BytesIO()
        fig.savefig(img, format="png", bbox_inches="tight", dpi=150)
        img.seek(0)
        plt.close(fig)
        return base64.b64encode(img.getvalue()).decode()

    @classmethod
    def generate_bar_chart(cls, labels, values, title, y_label=""):
        if not labels:
            return None

        plt.figure(figsize=(8, 4))
        bars = plt.bar(labels, values, color=cls.COLORS["green"], width=0.5)

        plt.title(title, color=cls.COLORS["black"], pad=15, fontweight="bold")
        plt.ylabel(y_label)
        plt.grid(axis="y", linestyle="--", alpha=0.5)
        plt.xticks(rotation=15 if len(labels) > 4 else 0)

        # Poner valores sobre las barras
        for bar in bars:
            height = bar.get_height()
            plt.text(
                bar.get_x() + bar.get_width() / 2.0,
                height,
                f"{height:.1f}",
                ha="center",
                va="bottom",
                fontsize=8,
            )

        plt.tight_layout()
        return cls._to_base64(plt.gcf())

    @classmethod
    def generate_pie_chart(cls, labels, values, title):
        if not labels:
            return None

        plt.figure(figsize=(6, 3.5))  # Slightly smaller height
        colors = [
            cls.COLORS["blue"],
            cls.COLORS["green"],
            cls.COLORS["red"],
            cls.COLORS["black"],
        ]

        # Ensure colors cycle if more labels than colors
        if len(labels) > len(colors):
            colors = colors * (len(labels) // len(colors) + 1)

        plt.pie(
            values,
            labels=labels,
            autopct="%1.1f%%",
            colors=colors[: len(labels)],
            startangle=90,
            textprops={"fontsize": 8},
        )
        plt.title(
            title, color=cls.COLORS["black"], fontweight="bold", fontsize=10, pad=10
        )

        plt.tight_layout()
        return cls._to_base64(plt.gcf())
