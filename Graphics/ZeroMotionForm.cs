using System;
using System.Drawing;
using System.Numerics;
using System.Threading.Tasks;
using System.Windows.Forms;

namespace Graphics
{
    // consumer: graph.zeros.motion.model
    // consumer: graph.zeros.motion.color
    // consumer: graph.zeros.motion.path
    // defines: graph.zeros.motion.ui
    internal sealed class ZeroMotionForm : Form
    {
        private readonly NumericUpDown parameter = new NumericUpDown
        {
            Minimum = -1, Maximum = 1, Value = 0.5m, DecimalPlaces = 6,
            Increment = 0.025m, Width = 108, AccessibleName = "Flow parameter lambda"
        };
        private readonly NumericUpDown rotation = new NumericUpDown
        {
            Minimum = 0, Maximum = 360, Value = 0, DecimalPlaces = 1,
            Increment = 22.5m, Width = 76, AccessibleName = "Palette rotation degrees"
        };
        private readonly TrackBar timeline = new TrackBar
        {
            Minimum = -1000, Maximum = 1000, Value = 500, TickFrequency = 250,
            SmallChange = 25, LargeChange = 100, Dock = DockStyle.Fill,
            AccessibleName = "Flow parameter timeline", Margin = Padding.Empty
        };
        private readonly Button play = new Button { Text = "Play toward collision", AutoSize = true };
        private readonly Button save = new Button { Text = "Save PNG + data", AutoSize = true, Enabled = false };
        private readonly Button tracePath = new Button { Text = "Trace two points", AutoSize = true };
        private readonly PictureBox picture = new PictureBox
        {
            Dock = DockStyle.Fill, SizeMode = PictureBoxSizeMode.Zoom,
            BackColor = Color.FromArgb(13, 17, 29), Margin = Padding.Empty
        };
        private readonly TextBox report = new TextBox
        {
            Dock = DockStyle.Fill, Multiline = true, ReadOnly = true,
            ScrollBars = ScrollBars.Vertical, BorderStyle = BorderStyle.None,
            Margin = new Padding(12, 6, 12, 6), Text = "Preparing the exact zero-motion example."
        };
        private readonly Timer animation = new Timer { Interval = 100 };
        private bool synchronizing, rendering, exporting;
        private int requestedVersion, displayedVersion = -1, collisionHold;
        private double displayedLambda, displayedRotation;
        private string frameReport = "";
        private Complex? pathStart, pathEnd;
        private bool choosingPath;
        private string pathReport = "";

        public ZeroMotionForm()
        {
            Text = "Zero motion color laboratory";
            AutoScaleMode = AutoScaleMode.Dpi;
            StartPosition = FormStartPosition.CenterScreen;
            ClientSize = new Size(1440, 1030);
            MinimumSize = new Size(960, 700);
            Size available = Screen.FromPoint(Cursor.Position).WorkingArea.Size;
            Size = new Size(Math.Min(Width, available.Width - 24), Math.Min(Height, available.Height - 24));

            var toolbar = new FlowLayoutPanel
            {
                Dock = DockStyle.Fill, AutoSize = true, WrapContents = true,
                Padding = new Padding(10), Margin = Padding.Empty
            };
            AddField(toolbar, "Flow parameter λ", parameter);
            AddField(toolbar, "Palette rotation °", rotation);
            toolbar.Controls.Add(play);
            AddPreset(toolbar, "Before: +0.5", 0.5m);
            AddPreset(toolbar, "Collision: 0", 0);
            AddPreset(toolbar, "After: −0.5", -0.5m);
            toolbar.Controls.Add(save);
            toolbar.Controls.Add(tracePath);
            var examplePath = new Button { Text = "Example path", AutoSize = true };
            toolbar.Controls.Add(examplePath);

            var strip = new TableLayoutPanel { Dock = DockStyle.Fill, ColumnCount = 3, Margin = Padding.Empty };
            strip.ColumnStyles.Add(new ColumnStyle(SizeType.Absolute, 125));
            strip.ColumnStyles.Add(new ColumnStyle(SizeType.Percent, 100));
            strip.ColumnStyles.Add(new ColumnStyle(SizeType.Absolute, 125));
            strip.Controls.Add(new Label { Text = "−1  imaginary zeros", AutoSize = true, Anchor = AnchorStyles.None }, 0, 0);
            strip.Controls.Add(timeline, 1, 0);
            strip.Controls.Add(new Label { Text = "real zeros  +1", AutoSize = true, Anchor = AnchorStyles.None }, 2, 0);

            var layout = new TableLayoutPanel
            {
                Dock = DockStyle.Fill, ColumnCount = 1, RowCount = 4,
                Margin = Padding.Empty, Padding = Padding.Empty
            };
            layout.ColumnStyles.Add(new ColumnStyle(SizeType.Percent, 100));
            layout.RowStyles.Add(new RowStyle(SizeType.AutoSize));
            layout.RowStyles.Add(new RowStyle(SizeType.Absolute, 42));
            layout.RowStyles.Add(new RowStyle(SizeType.Percent, 100));
            layout.RowStyles.Add(new RowStyle(SizeType.Absolute, 106));
            layout.Controls.Add(toolbar, 0, 0);
            layout.Controls.Add(strip, 0, 1);
            layout.Controls.Add(picture, 0, 2);
            layout.Controls.Add(report, 0, 3);
            Controls.Add(layout);

            parameter.ValueChanged += async (sender, args) =>
            {
                if (synchronizing) return;
                synchronizing = true;
                timeline.Value = (int)Math.Round(parameter.Value * 1000);
                synchronizing = false;
                await RequestRenderAsync();
            };
            timeline.ValueChanged += (sender, args) =>
            {
                if (!synchronizing) parameter.Value = timeline.Value / 1000m;
            };
            rotation.ValueChanged += async (sender, args) => await RequestRenderAsync();
            play.Click += (sender, args) =>
            {
                if (animation.Enabled) StopAnimation();
                else
                {
                    if (parameter.Value <= -1) parameter.Value = 1;
                    collisionHold = parameter.Value == 0 ? 7 : 0;
                    play.Text = "Pause";
                    animation.Start();
                }
            };
            animation.Tick += (sender, args) =>
            {
                if (rendering || exporting) return;
                if (collisionHold > 0) { collisionHold--; return; }
                if (parameter.Value <= -1) { StopAnimation(); return; }
                decimal next = Math.Max(-1, parameter.Value - 0.025m);
                if (parameter.Value > 0 && next <= 0) { next = 0; collisionHold = 7; }
                parameter.Value = next;
            };
            save.Click += async (sender, args) => await SaveAsync();
            tracePath.Click += (sender, args) =>
            {
                StopAnimation();
                choosingPath = !choosingPath;
                pathStart = pathEnd = null;
                pathReport = "";
                tracePath.Text = choosingPath ? "Cancel path" : "Trace two points";
                report.Text = choosingPath ? "Click the start point in any color panel, then click the end point." : frameReport;
                picture.Invalidate();
            };
            examplePath.Click += (sender, args) =>
            {
                StopAnimation();
                choosingPath = false;
                tracePath.Text = "Trace two points";
                pathStart = new Complex(-1.6, 0.7);
                pathEnd = new Complex(1.6, 0.7);
                UpdatePathReport();
            };
            picture.MouseMove += (sender, args) => InspectPoint(args.Location);
            picture.MouseLeave += (sender, args) => report.Text = pathReport.Length > 0 ? pathReport : frameReport;
            picture.MouseClick += (sender, args) => ChoosePathPoint(args.Location);
            picture.Paint += (sender, args) => PaintPath(args.Graphics);
            Shown += async (sender, args) => await RequestRenderAsync();
        }

        private static void AddField(FlowLayoutPanel toolbar, string label, Control control)
        {
            var group = new FlowLayoutPanel { AutoSize = true, WrapContents = false, Margin = new Padding(0, 0, 12, 0) };
            group.Controls.Add(new Label { Text = label, AutoSize = true, Margin = new Padding(0, 6, 6, 0) });
            group.Controls.Add(control);
            toolbar.Controls.Add(group);
        }

        private void AddPreset(FlowLayoutPanel toolbar, string text, decimal value)
        {
            var button = new Button { Text = text, AutoSize = true };
            button.Click += (sender, args) => { StopAnimation(); parameter.Value = value; };
            toolbar.Controls.Add(button);
        }

        private void StopAnimation()
        {
            animation.Stop();
            collisionHold = 0;
            play.Text = "Play toward collision";
        }

        private async Task RequestRenderAsync()
        {
            requestedVersion++;
            if (rendering || IsDisposed || Disposing) return;
            rendering = true;
            save.Enabled = false;
            try
            {
                // Coalesce slider input so an old frame never overwrites a newer request.
                while (!IsDisposed && !Disposing && displayedVersion != requestedVersion)
                {
                    int version = requestedVersion;
                    double lambda = (double)parameter.Value, degrees = (double)rotation.Value;
                    var frame = await Task.Run(() =>
                    {
                        Bitmap image = ZeroMotionExperiment.Render(lambda, degrees, out string text);
                        return (Image: image, Report: text);
                    });
                    if (IsDisposed || Disposing) { frame.Image.Dispose(); return; }
                    if (version != requestedVersion) { frame.Image.Dispose(); continue; }
                    Image old = picture.Image;
                    picture.Image = frame.Image;
                    old?.Dispose();
                    frameReport = frame.Report + "\r\nMove the pointer over a color panel to inspect its local coordinates and angles.";
                    report.Text = frameReport;
                    displayedLambda = lambda;
                    displayedRotation = degrees;
                    displayedVersion = version;
                    UpdatePathReport();
                }
            }
            catch (Exception error)
            {
                if (!IsDisposed && !Disposing)
                {
                    StopAnimation();
                    report.Text = "The zero-motion view could not be rendered: " + error.Message;
                }
            }
            finally
            {
                rendering = false;
                if (!IsDisposed && !Disposing) save.Enabled = picture.Image != null && !exporting;
            }
        }

        private void InspectPoint(Point point)
        {
            if (pathReport.Length > 0 || choosingPath) return;
            if (MapPoint(point, out var z))
                report.Text = ZeroMotionExperiment.DescribePoint(z, displayedLambda, displayedRotation);
            else report.Text = frameReport;
        }

        private bool MapPoint(Point point, out Complex z)
        {
            z = Complex.Zero;
            if (picture.Image == null || displayedVersion < 0) return false;
            double scale = Math.Min((double)picture.ClientSize.Width / picture.Image.Width,
                (double)picture.ClientSize.Height / picture.Image.Height);
            if (scale <= 0) return false;
            float x = (float)((point.X - (picture.ClientSize.Width - picture.Image.Width * scale) / 2) / scale);
            float y = (float)((point.Y - (picture.ClientSize.Height - picture.Image.Height * scale) / 2) / scale);
            return ZeroMotionExperiment.TryMapPixel(x, y, out z);
        }

        private void ChoosePathPoint(Point point)
        {
            if (!choosingPath || rendering || !MapPoint(point, out var z)) return;
            if (pathStart == null)
            {
                pathStart = z;
                report.Text = "Start selected. Click an end point in any color panel.";
            }
            else
            {
                pathEnd = z;
                choosingPath = false;
                tracePath.Text = "Clear / new path";
                UpdatePathReport();
            }
            picture.Invalidate();
        }

        private void UpdatePathReport()
        {
            if (pathStart != null && pathEnd != null && displayedVersion >= 0)
            {
                pathReport = ZeroMotionPath.Describe(pathStart.Value, pathEnd.Value, displayedLambda, displayedRotation);
                report.Text = pathReport;
            }
            picture.Invalidate();
        }

        private void PaintPath(System.Drawing.Graphics graphics)
        {
            if (pathStart == null || picture.Image == null) return;
            float scale = Math.Min((float)picture.ClientSize.Width / picture.Image.Width,
                (float)picture.ClientSize.Height / picture.Image.Height);
            float left = (picture.ClientSize.Width - picture.Image.Width * scale) / 2;
            float top = (picture.ClientSize.Height - picture.Image.Height * scale) / 2;
            DrawPathOverlay(graphics, scale, left, top, pathStart.Value, pathEnd);
        }

        private static void DrawPathOverlay(System.Drawing.Graphics graphics, float scale, float left, float top, Complex startPoint, Complex? endPoint)
        {
            using var outline = new Pen(Color.FromArgb(220, 10, 12, 20), 4);
            using var line = new Pen(Color.White, 1.7f) { EndCap = System.Drawing.Drawing2D.LineCap.ArrowAnchor };
            using var font = new Font("Segoe UI", 10, FontStyle.Bold);
            graphics.SmoothingMode = System.Drawing.Drawing2D.SmoothingMode.AntiAlias;
            for (int panel = 0; panel < 3; panel++)
            {
                PointF Map(Complex z) => new PointF(left + (72 + 468 * panel + (float)(z.Real + 2) * 90) * scale,
                    top + (203 + (float)(2 - z.Imaginary) * 90) * scale);
                PointF start = Map(startPoint);
                if (endPoint != null)
                {
                    PointF end = Map(endPoint.Value);
                    graphics.DrawLine(outline, start, end);
                    graphics.DrawLine(line, start, end);
                    graphics.DrawString("E", font, Brushes.White, end.X + 5, end.Y - 18);
                }
                graphics.FillEllipse(Brushes.White, start.X - 3, start.Y - 3, 6, 6);
                graphics.DrawString("S", font, Brushes.White, start.X + 5, start.Y - 18);
            }
        }

        private async Task SaveAsync()
        {
            if (picture.Image == null || rendering || exporting) return;
            StopAnimation();
            double lambda = displayedLambda, degrees = displayedRotation;
            Complex? start = pathStart, end = pathEnd;
            using var dialog = new SaveFileDialog
            {
                Title = "Save zero-motion image and numerical data", FileName = "zero-motion.png",
                Filter = "PNG image (*.png)|*.png", DefaultExt = "png", AddExtension = true,
                RestoreDirectory = true
            };
            if (dialog.ShowDialog(this) != DialogResult.OK) return;
            exporting = true;
            save.Enabled = false;
            try
            {
                await Task.Run(() => ExportFrame(dialog.FileName, lambda, degrees, start, end));
            }
            catch (Exception error)
            {
                if (!IsDisposed && !Disposing)
                    MessageBox.Show(this, error.Message, "Save zero-motion view", MessageBoxButtons.OK, MessageBoxIcon.Error);
            }
            finally
            {
                exporting = false;
                if (!IsDisposed && !Disposing) save.Enabled = picture.Image != null && !rendering;
            }
        }

        internal static void ExportFrame(string path, double lambda, double degrees, Complex? start, Complex? end)
        {
            ZeroMotionExperiment.Export(path, lambda, degrees);
            if (start == null || end == null) return;
            using var image = ZeroMotionExperiment.Render(lambda, degrees, out _);
            using (var g = System.Drawing.Graphics.FromImage(image))
                DrawPathOverlay(g, 1, 0, 0, start.Value, end.Value);
            image.Save(path, System.Drawing.Imaging.ImageFormat.Png);
            System.IO.File.WriteAllText(System.IO.Path.ChangeExtension(path, ".path.json"),
                System.Text.Json.JsonSerializer.Serialize(ZeroMotionPath.Analyze(start.Value, end.Value, lambda, degrees),
                    new System.Text.Json.JsonSerializerOptions { WriteIndented = true }));
            System.IO.File.WriteAllText(System.IO.Path.ChangeExtension(path, ".path.txt"),
                ZeroMotionPath.Describe(start.Value, end.Value, lambda, degrees));
        }

        protected override void Dispose(bool disposing)
        {
            if (disposing)
            {
                animation.Stop();
                animation.Dispose();
                picture.Image?.Dispose();
                picture.Image = null;
            }
            base.Dispose(disposing);
        }
    }
}
