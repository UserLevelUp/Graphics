using System;
using System.Drawing;
using System.Numerics;
using System.Threading.Tasks;
using System.Windows.Forms;

namespace Graphics
{
    // defines: graph.riemann.switch.ui
    // consumes: graph.riemann.switch.model
    internal sealed class ZetaSwitchForm : Form
    {
        private readonly PictureBox picture = new PictureBox { Dock = DockStyle.Fill, SizeMode = PictureBoxSizeMode.Zoom, BackColor = Color.FromArgb(14, 19, 29) };
        private readonly NumericUpDown lower = Number(10, 10, 30, 2, 0.1m);
        private readonly NumericUpDown upper = Number(30, 10, 30, 2, 0.1m);
        private readonly NumericUpDown rotation = Number(0, 0, 360, 0, 15);
        private readonly ComboBox resolution = new ComboBox { DropDownStyle = ComboBoxStyle.DropDownList, Width = 72 };
        private readonly CheckBox markers = new CheckBox { Text = "Zero / 1-point markers", Checked = true, AutoSize = true };
        private readonly Button save = new Button { Text = "Save image + data", AutoSize = true, Enabled = false };
        private readonly Label status = new Label { Dock = DockStyle.Fill, AutoEllipsis = true, Padding = new Padding(10, 5, 10, 0) };
        private ZetaSwitchExperiment.Frame displayed;
        private int requestedVersion, displayedVersion = -1;
        private double displayedRotation;
        private bool rendering, settingPreset;

        public ZetaSwitchForm()
        {
            Text = "Zeta unit-term switch laboratory";
            StartPosition = FormStartPosition.CenterParent;
            ClientSize = new Size(1280, 900);
            MinimumSize = new Size(960, 700);
            Font = new Font("Segoe UI", 9);
            BackColor = Color.FromArgb(242, 245, 249);
            var layout = new TableLayoutPanel { Dock = DockStyle.Fill, ColumnCount = 1, RowCount = 4 };
            layout.RowStyles.Add(new RowStyle(SizeType.AutoSize));
            layout.RowStyles.Add(new RowStyle(SizeType.AutoSize));
            layout.RowStyles.Add(new RowStyle(SizeType.Percent, 100));
            layout.RowStyles.Add(new RowStyle(SizeType.Absolute, 92));
            var controls = new FlowLayoutPanel { Dock = DockStyle.Fill, AutoSize = true, Padding = new Padding(8), WrapContents = true };
            void Label(string text) => controls.Controls.Add(new Label { Text = text, AutoSize = true, Margin = new Padding(7, 7, 2, 0) });
            Label("Height from"); controls.Controls.Add(lower);
            Label("to"); controls.Controls.Add(upper);
            Label("Grid"); resolution.Items.AddRange(new object[] { 128, 256, 384 }); resolution.SelectedIndex = 1; controls.Controls.Add(resolution);
            Label("Palette °"); controls.Controls.Add(rotation); controls.Controls.Add(markers);
            var render = new Button { Text = "Render", AutoSize = true }; controls.Controls.Add(render); controls.Controls.Add(save);
            var presets = new FlowLayoutPanel { Dock = DockStyle.Fill, AutoSize = true, Padding = new Padding(8, 0, 8, 3) };
            void Preset(string title, decimal min, decimal max)
            {
                var button = new Button { Text = title, AutoSize = true };
                button.Click += (_, __) => { settingPreset = true; lower.Value = min; upper.Value = max; settingPreset = false; RequestRender(); };
                presets.Controls.Add(button);
            }
            Preset("Overview", 10, 30); Preset("First zeta zero", 13.9m, 14.4m); Preset("A zeta 1-point", 23.1m, 23.6m);
            presets.Controls.Add(new Label { Text = "W selects ζ or ζ−1. G=ζ(ζ−1) compares the same zero sets without a switching jump.", AutoSize = true, Margin = new Padding(12, 8, 0, 0) });
            layout.Controls.Add(controls, 0, 0); layout.Controls.Add(presets, 0, 1); layout.Controls.Add(picture, 0, 2); layout.Controls.Add(status, 0, 3);
            Controls.Add(layout);
            lower.ValueChanged += (_, __) => RequestRender(); upper.ValueChanged += (_, __) => RequestRender();
            rotation.ValueChanged += (_, __) => RequestRender(); resolution.SelectedIndexChanged += (_, __) => RequestRender(); markers.CheckedChanged += (_, __) => RequestRender();
            render.Click += (_, __) => RequestRender(); save.Click += (_, __) => SaveFrame();
            picture.MouseMove += (_, e) => Inspect(e.Location);
            picture.MouseLeave += (_, __) => { if (!rendering && displayed != null && displayedVersion == requestedVersion) status.Text = Summary(displayed); };
            Shown += (_, __) => RequestRender();
        }

        private static NumericUpDown Number(decimal value, decimal minimum, decimal maximum, int places, decimal increment)
            => new NumericUpDown { Value = value, Minimum = minimum, Maximum = maximum, DecimalPlaces = places, Increment = increment, Width = 76 };

        private void RequestRender()
        {
            if (settingPreset || IsDisposed || Disposing) return;
            requestedVersion++;
            save.Enabled = false;
            if (!rendering) _ = RenderAsync();
        }

        private async Task RenderAsync()
        {
            rendering = true;
            try
            {
                while (!IsDisposed && !Disposing && displayedVersion != requestedVersion)
                {
                    int version = requestedVersion;
                    double min = (double)lower.Value, max = (double)upper.Value, degrees = (double)rotation.Value;
                    if (max <= min) { status.Text = "Choose an upper height greater than the lower height."; return; }
                    int grid = (int)resolution.SelectedItem;
                    bool show = markers.Checked;
                    status.Text = $"Computing {grid} × {grid} shared samples…";
                    var frame = await Task.Run(() => ZetaSwitchExperiment.Compute(min, max, grid, degrees, show));
                    if (IsDisposed || Disposing) { frame.Dispose(); return; }
                    if (version != requestedVersion) { frame.Dispose(); continue; }
                    var old = displayed;
                    displayed = frame;
                    picture.Image = frame.Image;
                    old?.Dispose();
                    displayedVersion = version; displayedRotation = degrees;
                    status.Text = Summary(frame);
                }
            }
            catch (Exception error)
            {
                if (!IsDisposed && !Disposing) status.Text = "Unable to render: " + error.Message;
            }
            finally
            {
                rendering = false;
                if (!IsDisposed && !Disposing) save.Enabled = displayed != null && displayedVersion == requestedVersion;
            }
        }

        private void Inspect(Point point)
        {
            if (rendering || displayed == null || displayedVersion != requestedVersion) return;
            double scale = Math.Min((double)picture.ClientSize.Width / displayed.Image.Width, (double)picture.ClientSize.Height / displayed.Image.Height);
            if (scale <= 0) return;
            float x = (float)((point.X - (picture.ClientSize.Width - displayed.Image.Width * scale) / 2) / scale);
            float y = (float)((point.Y - (picture.ClientSize.Height - displayed.Image.Height * scale) / 2) / scale);
            status.Text = ZetaSwitchExperiment.TryMapPixel(displayed, x, y, out Complex s)
                ? ZetaSwitchExperiment.DescribePoint(s, displayedRotation) : Summary(displayed);
        }

        private static string Summary(ZetaSwitchExperiment.Frame frame)
        {
            string[] lines = frame.Report.Split('\n');
            return lines[0] + "\n" + lines[1] + "\n" + lines[lines.Length - 1]
                + "\nHover over a panel to inspect its values. Save includes the full report and numerical samples.";
        }

        private void SaveFrame()
        {
            if (rendering || displayed == null || displayedVersion != requestedVersion) return;
            using var dialog = new SaveFileDialog { Title = "Save switch image and numerical data", Filter = "PNG image (*.png)|*.png", FileName = "zeta-switch.png", DefaultExt = "png", AddExtension = true, RestoreDirectory = true };
            if (dialog.ShowDialog(this) != DialogResult.OK) return;
            try
            {
                // Export exactly the displayed frame; do not recompute or read pending control values.
                ZetaSwitchExperiment.Export(dialog.FileName, displayed);
                status.Text = "Saved PNG, raw values JSON, and text report: " + dialog.FileName;
            }
            catch (Exception error) { MessageBox.Show(this, error.Message, "Save switch view", MessageBoxButtons.OK, MessageBoxIcon.Error); }
        }

        protected override void Dispose(bool disposing)
        {
            if (disposing) { picture.Image = null; displayed?.Dispose(); displayed = null; }
            base.Dispose(disposing);
        }
    }
}
