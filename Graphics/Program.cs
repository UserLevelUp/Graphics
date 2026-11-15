using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;
using System.Windows.Forms;

namespace Graphics
{
    static class Program
    {
        /// <summary>
        ///  The main entry point for the application.
        /// </summary>
        [STAThread]
        static void Main(string[] args)
        {
            if (args.Length == 8 && args[0] == "--zero-path")
            {
                double Parse(int i) => double.Parse(args[i], System.Globalization.CultureInfo.InvariantCulture);
                var start = new System.Numerics.Complex(Parse(3), Parse(4));
                var end = new System.Numerics.Complex(Parse(5), Parse(6));
                ZeroMotionForm.ExportFrame(System.IO.Path.ChangeExtension(args[1], ".png"), Parse(2), Parse(7), start, end);
                System.IO.File.WriteAllText(args[1], System.Text.Json.JsonSerializer.Serialize(new
                {
                    analysis = ZeroMotionPath.Analyze(start, end, Parse(2), Parse(7)),
                    verification = ZeroMotionPath.Verify()
                }, new System.Text.Json.JsonSerializerOptions { WriteIndented = true }));
                return;
            }
            if ((args.Length == 2 || args.Length == 3 || args.Length == 4) && args[0] == "--zero-motion")
            {
                double lambda = args.Length >= 3 ? double.Parse(args[2], System.Globalization.CultureInfo.InvariantCulture) : 0.5;
                double rotation = args.Length == 4 ? double.Parse(args[3], System.Globalization.CultureInfo.InvariantCulture) : 0;
                ZeroMotionExperiment.Export(args[1], lambda, rotation);
                return;
            }
            if (args.Length == 2 && args[0] == "--prime-unwrap")
            {
                using var image = PrimeUnwrap.Render(1.2, 13, out string report);
                image.Save(args[1], System.Drawing.Imaging.ImageFormat.Png);
                System.IO.File.WriteAllText(System.IO.Path.ChangeExtension(args[1], ".txt"), report);
                System.IO.File.WriteAllText(System.IO.Path.ChangeExtension(args[1], ".json"),
                    System.Text.Json.JsonSerializer.Serialize(PrimeUnwrap.Verify(), new System.Text.Json.JsonSerializerOptions { WriteIndented = true }));
                return;
            }
            if ((args.Length == 2 || args.Length == 7 || args.Length == 8) && args[0] == "--prime-phase")
            {
                if (args.Length == 2) PrimePhaseExperiment.Export(args[1]);
                else PrimePhaseExperiment.Export(args[1], double.Parse(args[2], System.Globalization.CultureInfo.InvariantCulture),
                    int.Parse(args[3]), double.Parse(args[4], System.Globalization.CultureInfo.InvariantCulture), int.Parse(args[5]), bool.Parse(args[6]),
                    args.Length == 8 && bool.Parse(args[7]));
                return;
            }
            if (args.Length == 2 && (args[0] == "--zeta-preview" || args[0] == "--zeta-contours" || args[0] == "--zeta-origins"))
            {
                string report;
                using var preview = args[0] switch
                {
                    "--zeta-origins" => ZetaOrigins.Render(out report),
                    "--zeta-contours" => ZetaContours.Render(out report),
                    _ => ZetaExperiment.Render(out report)
                };
                preview.Save(args[1], System.Drawing.Imaging.ImageFormat.Png);
                Console.WriteLine(report);
                return;
            }

            Application.SetHighDpiMode(HighDpiMode.SystemAware);
            Application.EnableVisualStyles();
            Application.SetCompatibleTextRenderingDefault(false);
            Application.Run(args.Length == 1 && args[0] == "--zero-lab" ? (Form)new ZeroMotionForm()
                : args.Length == 1 && args[0] == "--prime-lab" ? (Form)new PrimePhaseForm() : new GraphForm());
        }
    }
}
