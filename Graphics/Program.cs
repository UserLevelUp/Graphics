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
            Application.Run(new GraphForm());
        }
    }
}
