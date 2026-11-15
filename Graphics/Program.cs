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
            // produces: graph.riemann.continuation.animation.export
            if (args.Length >= 2 && args.Length <= 5 && args[0] == "--zeta-continuation")
            {
                double Parse(int index) => double.Parse(args[index], System.Globalization.CultureInfo.InvariantCulture);
                var paths = ZetaContinuationExperiment.ComputePaths();
                using var frame = ZetaContinuationExperiment.Render(paths, args.Length >= 3 ? Parse(2) : 0,
                    args.Length >= 4 ? int.Parse(args[3]) : 256, args.Length == 5 ? Parse(4) : 0);
                ZetaContinuationExperiment.Export(args[1], frame);
                return;
            }
            if (args.Length == 2 && args[0] == "--verify-continuation")
            {
                string path = System.IO.Path.GetFullPath(args[1]);
                System.IO.Directory.CreateDirectory(System.IO.Path.GetDirectoryName(path));
                System.IO.File.WriteAllText(path, ZetaContinuationExperiment.Verify(ZetaContinuationExperiment.ComputePaths()));
                return;
            }
            if ((args.Length == 3 || args.Length == 4) && args[0] == "--continuation-sequence")
            {
                string directory = System.IO.Path.GetFullPath(args[1]);
                int count = int.Parse(args[2]);
                int resolution = args.Length == 4 ? int.Parse(args[3]) : 256;
                if (count < 2 || count > 10000) throw new ArgumentOutOfRangeException(nameof(count), "Use 2 through 10000 sequence frames.");
                var paths = ZetaContinuationExperiment.ComputePaths();
                ZetaContinuationExperiment.Verify(paths);
                System.IO.Directory.CreateDirectory(directory);
                for (int index = 0; index < count; index++)
                {
                    using var phase = ZetaContinuationExperiment.RenderPhase((double)index / (count - 1), resolution);
                    phase.Save(System.IO.Path.Combine(directory, $"phase{index:D4}.png"), System.Drawing.Imaging.ImageFormat.Png);
                }
                using var frame = ZetaContinuationExperiment.Render(paths, 1, resolution);
                ZetaContinuationExperiment.Export(System.IO.Path.Combine(directory, "paths.png"), frame);
                System.IO.File.WriteAllText(System.IO.Path.Combine(directory, "sequence.json"),
                    System.Text.Json.JsonSerializer.Serialize(new
                    {
                        schema = "graph-zeta-continuation-sequence-v1", traceId = "graph.riemann.continuation.animation",
                        count, resolution, paletteDegrees = 0, filenamePattern = "phase{index:D4}.png",
                        targetFormula = "a=index/(count-1)", targetMinimum = 0, targetMaximum = 1,
                        domain = new { minSigma = 0.05, maxSigma = 3, minT = 10, maxT = 30 },
                        note = "Phase-only numerical raster; paths and text remain separate. Not an RH proof."
                    }, new System.Text.Json.JsonSerializerOptions { WriteIndented = true }));
                return;
            }
            // produces: graph.riemann.switch.export
            if ((args.Length == 2 || args.Length == 7) && args[0] == "--zeta-switch")
            {
                double Parse(int i) => double.Parse(args[i], System.Globalization.CultureInfo.InvariantCulture);
                using var frame = args.Length == 2 ? ZetaSwitchExperiment.Compute(10, 30, 256, 0)
                    : ZetaSwitchExperiment.Compute(Parse(2), Parse(3), int.Parse(args[4]), Parse(5), bool.Parse(args[6]));
                ZetaSwitchExperiment.Export(args[1], frame);
                return;
            }
            if (args.Length == 2 && args[0] == "--verify-switch")
            {
                System.IO.File.WriteAllText(args[1], ZetaSwitchExperiment.Verify());
                return;
            }
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
            Application.Run(args.Length == 1 && args[0] == "--continuation-lab" ? (Form)new ZetaContinuationForm()
                : args.Length == 1 && args[0] == "--switch-lab" ? (Form)new ZetaSwitchForm()
                : args.Length == 1 && args[0] == "--zero-lab" ? (Form)new ZeroMotionForm()
                : args.Length == 1 && args[0] == "--prime-lab" ? (Form)new PrimePhaseForm() : new GraphForm());
        }
    }
}
