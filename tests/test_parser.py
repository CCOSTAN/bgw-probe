import unittest

from bgw_probe.parser import parse_label_value_rows


class ParserTests(unittest.TestCase):
    def test_table_parser_normalizes_labels_and_values(self) -> None:
        html = """
        <table>
          <tr><th>Model Number:</th><td> BGW210-700 </td></tr>
          <tr><td>Software Version</td><td><span>4.28.8</span></td></tr>
        </table>
        """
        self.assertEqual(
            parse_label_value_rows(html),
            {
                "Model Number": "BGW210-700",
                "Software Version": "4.28.8",
            },
        )


if __name__ == "__main__":
    unittest.main()
