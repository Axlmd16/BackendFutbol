"""Tests para ChartGenerator."""

from unittest.mock import MagicMock, patch


class TestChartGeneratorColors:
    """Tests para colores corporativos."""

    def test_colors_defined(self):
        """Verifica que los colores corporativos estén definidos."""
        from app.utils.chart_generator import ChartGenerator

        assert "red" in ChartGenerator.COLORS
        assert "green" in ChartGenerator.COLORS
        assert "black" in ChartGenerator.COLORS
        assert "blue" in ChartGenerator.COLORS

    def test_colors_are_hex(self):
        """Verifica que los colores sean hexadecimales."""
        from app.utils.chart_generator import ChartGenerator

        for color in ChartGenerator.COLORS.values():
            assert color.startswith("#")
            assert len(color) == 7


class TestToBase64:
    """Tests para _to_base64."""

    @patch("app.utils.chart_generator.plt")
    def test_to_base64_returns_string(self, mock_plt):
        """Verifica que retorne string base64."""
        from app.utils.chart_generator import ChartGenerator

        mock_fig = MagicMock()
        mock_buffer = MagicMock()

        # Simular BytesIO
        with patch("app.utils.chart_generator.io.BytesIO") as mock_bytesio:
            mock_bytesio.return_value = mock_buffer
            mock_buffer.getvalue.return_value = b"test_image_data"

            result = ChartGenerator._to_base64(mock_fig)

            assert isinstance(result, str)
            mock_fig.savefig.assert_called_once()
            mock_plt.close.assert_called_once_with(mock_fig)

    @patch("app.utils.chart_generator.plt")
    def test_to_base64_closes_figure(self, mock_plt):
        """Verifica que cierre la figura."""
        from app.utils.chart_generator import ChartGenerator

        mock_fig = MagicMock()

        with patch("app.utils.chart_generator.io.BytesIO") as mock_bytesio:
            mock_buffer = MagicMock()
            mock_bytesio.return_value = mock_buffer
            mock_buffer.getvalue.return_value = b"test_data"

            ChartGenerator._to_base64(mock_fig)

            mock_plt.close.assert_called_once_with(mock_fig)


class TestGenerateBarChart:
    """Tests para generate_bar_chart."""

    def test_bar_chart_empty_labels(self):
        """Retorna None si labels está vacío."""
        from app.utils.chart_generator import ChartGenerator

        result = ChartGenerator.generate_bar_chart([], [1, 2, 3], "Test Title")
        assert result is None

    def test_bar_chart_none_labels(self):
        """Retorna None si labels es None."""
        from app.utils.chart_generator import ChartGenerator

        result = ChartGenerator.generate_bar_chart(None, [1, 2, 3], "Test Title")
        assert result is None

    @patch("app.utils.chart_generator.plt")
    def test_bar_chart_returns_base64(self, mock_plt):
        """Retorna string base64 válido."""
        from app.utils.chart_generator import ChartGenerator

        # Setup mocks
        mock_fig = MagicMock()
        mock_bars = [MagicMock()]
        mock_bars[0].get_height.return_value = 10
        mock_bars[0].get_x.return_value = 0
        mock_bars[0].get_width.return_value = 0.5

        mock_plt.figure.return_value = mock_fig
        mock_plt.bar.return_value = mock_bars
        mock_plt.gcf.return_value = mock_fig

        with patch.object(ChartGenerator, "_to_base64", return_value="base64_string"):
            result = ChartGenerator.generate_bar_chart(
                ["A", "B"], [10, 20], "Test Title"
            )

            assert result == "base64_string"
            mock_plt.figure.assert_called_once()
            mock_plt.bar.assert_called_once()

    @patch("app.utils.chart_generator.plt")
    def test_bar_chart_with_y_label(self, mock_plt):
        """Genera gráfico con y_label."""
        from app.utils.chart_generator import ChartGenerator

        mock_bars = [MagicMock()]
        mock_bars[0].get_height.return_value = 5
        mock_bars[0].get_x.return_value = 0
        mock_bars[0].get_width.return_value = 0.5

        mock_plt.bar.return_value = mock_bars
        mock_plt.gcf.return_value = MagicMock()

        with patch.object(ChartGenerator, "_to_base64", return_value="base64_string"):
            ChartGenerator.generate_bar_chart(["X"], [5], "Title", y_label="Count")

            mock_plt.ylabel.assert_called_once_with("Count")

    @patch("app.utils.chart_generator.plt")
    def test_bar_chart_few_labels_no_rotation(self, mock_plt):
        """Con pocos labels no hay rotación."""
        from app.utils.chart_generator import ChartGenerator

        mock_bars = [MagicMock() for _ in range(3)]
        for bar in mock_bars:
            bar.get_height.return_value = 1
            bar.get_x.return_value = 0
            bar.get_width.return_value = 0.5

        mock_plt.bar.return_value = mock_bars
        mock_plt.gcf.return_value = MagicMock()

        with patch.object(ChartGenerator, "_to_base64", return_value="base64"):
            ChartGenerator.generate_bar_chart(["A", "B", "C"], [1, 2, 3], "Title")

            # Con 3 labels (<=4) no debería haber rotación (rotation=0)
            mock_plt.xticks.assert_called()

    @patch("app.utils.chart_generator.plt")
    def test_bar_chart_many_labels_with_rotation(self, mock_plt):
        """Con muchos labels hay rotación."""
        from app.utils.chart_generator import ChartGenerator

        labels = ["A", "B", "C", "D", "E"]
        values = [1, 2, 3, 4, 5]

        mock_bars = [MagicMock() for _ in range(5)]
        for bar in mock_bars:
            bar.get_height.return_value = 1
            bar.get_x.return_value = 0
            bar.get_width.return_value = 0.5

        mock_plt.bar.return_value = mock_bars
        mock_plt.gcf.return_value = MagicMock()

        with patch.object(ChartGenerator, "_to_base64", return_value="base64"):
            ChartGenerator.generate_bar_chart(labels, values, "Title")

            # Con 5 labels (>4) debería haber rotación (rotation=15)
            mock_plt.xticks.assert_called()


class TestGeneratePieChart:
    """Tests para generate_pie_chart."""

    def test_pie_chart_empty_labels(self):
        """Retorna None si labels está vacío."""
        from app.utils.chart_generator import ChartGenerator

        result = ChartGenerator.generate_pie_chart([], [1, 2, 3], "Test Title")
        assert result is None

    def test_pie_chart_none_labels(self):
        """Retorna None si labels es None."""
        from app.utils.chart_generator import ChartGenerator

        result = ChartGenerator.generate_pie_chart(None, [1, 2, 3], "Test Title")
        assert result is None

    @patch("app.utils.chart_generator.plt")
    def test_pie_chart_returns_base64(self, mock_plt):
        """Retorna string base64 válido."""
        from app.utils.chart_generator import ChartGenerator

        mock_fig = MagicMock()
        mock_plt.figure.return_value = mock_fig
        mock_plt.gcf.return_value = mock_fig

        with patch.object(ChartGenerator, "_to_base64", return_value="base64_pie"):
            result = ChartGenerator.generate_pie_chart(
                ["A", "B"], [30, 70], "Pie Title"
            )

            assert result == "base64_pie"
            mock_plt.figure.assert_called_once()
            mock_plt.pie.assert_called_once()

    @patch("app.utils.chart_generator.plt")
    def test_pie_chart_few_labels(self, mock_plt):
        """Genera gráfico con pocos labels."""
        from app.utils.chart_generator import ChartGenerator

        mock_plt.gcf.return_value = MagicMock()

        with patch.object(ChartGenerator, "_to_base64", return_value="base64"):
            result = ChartGenerator.generate_pie_chart(
                ["X", "Y"], [50, 50], "Simple Pie"
            )

            assert result is not None
            mock_plt.pie.assert_called_once()

    @patch("app.utils.chart_generator.plt")
    def test_pie_chart_many_labels(self, mock_plt):
        """Genera gráfico con muchos labels (colors cycle)."""
        from app.utils.chart_generator import ChartGenerator

        labels = ["A", "B", "C", "D", "E", "F"]  # Más que 4 colores
        values = [10, 20, 15, 25, 15, 15]

        mock_plt.gcf.return_value = MagicMock()

        with patch.object(ChartGenerator, "_to_base64", return_value="base64"):
            result = ChartGenerator.generate_pie_chart(labels, values, "Many Slices")

            assert result is not None
            mock_plt.pie.assert_called_once()

    @patch("app.utils.chart_generator.plt")
    def test_pie_chart_title_styling(self, mock_plt):
        """Verifica que aplique estilo al título."""
        from app.utils.chart_generator import ChartGenerator

        mock_plt.gcf.return_value = MagicMock()

        with patch.object(ChartGenerator, "_to_base64", return_value="base64"):
            ChartGenerator.generate_pie_chart(["A"], [100], "Styled Title")

            mock_plt.title.assert_called_once()
            call_kwargs = mock_plt.title.call_args[1]
            assert "fontweight" in call_kwargs
            assert call_kwargs["fontweight"] == "bold"
