using System;
using System.Drawing;
using System.Numerics;
using System.Threading.Tasks;
using System.Windows.Forms;

namespace Graphics
{
    // defines: graph.riemann.continuation.animation.ui
    // consumer: graph.riemann.continuation.animation.model
    internal sealed class ZetaContinuationForm : Form
    {
        private readonly PictureBox picture = new PictureBox { Dock = DockStyle.Fill, SizeMode = PictureBoxSizeMode.Zoom, BackColor = Color.FromArgb(13, 18, 30) };
        private readonly NumericUpDown target = new NumericUpDown { Minimum = 0, Maximum = 1, DecimalPlaces = 3, Increment = 0.01m, Width = 86, AccessibleName = "Real zeta target a" };
        private readonly NumericUpDown rotation = new NumericUpDown { Minimum = 0, Maximum = 360, Increment = 15, Width = 72, AccessibleName = "Palette rotation degrees" };
        private readonly ComboBox resolution = new ComboBox { DropDownStyle = ComboBoxStyle.DropDownList, Width = 76 };
        private readonly TrackBar timeline = new TrackBar { Minimum = 0, Maximum = 1000, TickFrequency = 100, SmallChange = 10, LargeChange = 100, Dock = DockStyle.Fill, AccessibleName = "Real target timeline" };
        private readonly Button play = new Button { Text = "Play", AutoSize = true, Enabled = false };
        private readonly Button save = new Button { Text = "Save image + data", AutoSize = true, Enabled = false };
        private readonly Label status = new Label { Dock = DockStyle.Fill, Padding = new Padding(10, 5, 10, 0), AutoEllipsis = true };
        private readonly Timer animation = new Timer { Interval = 180 };
        private ZetaContinuationExperiment.ContinuationData paths;
        private ZetaContinuationExperiment.Frame displayed;
        private bool rendering, synchronizing, playing;
        private int requestedVersion, displayedVersion = -1;

        internal ZetaContinuationForm()
        {
            Text = "Zeta real-target continuation laboratory";
            ClientSize = new Size(1280, 940);
            MinimumSize = new Size(1000, 720);
            StartPosition = FormStartPosition.CenterScreen;
            Font = new Font("Segoe UI", 9);
            BackColor = Color.FromArgb(242, 245, 249);
            var layout = new TableLayoutPanel { Dock = DockStyle.Fill, ColumnCount = 1, RowCount = 4 };
            layout.RowStyles.Add(new RowStyle(SizeType.AutoSize));
            layout.RowStyles.Add(new RowStyle(SizeType.Absolute, 46));
            layout.RowStyles.Add(new RowStyle(SizeType.Percent, 100));
            layout.RowStyles.Add(new RowStyle(SizeType.Absolute, 100));
            var controls = new FlowLayoutPanel { Dock = DockStyle.Fill, AutoSize = true, Padding = new Padding(8), WrapContents = true };
            void Label(string text) => controls.Controls.Add(new Label { Text = text, AutoSize = true, Margin = new Padding(8, 7, 2, 0) });
            Label("Target a"); controls.Controls.Add(target); controls.Controls.Add(play);
            var reset = new Button { Text = "Reset to zero", AutoSize = true }; controls.Controls.Add(reset);
            var end = new Button { Text = "Target one", AutoSize = true }; controls.Controls.Add(end);
            Label("Grid"); resolution.Items.AddRange(new object[] { 128, 256, 384 }); resolution.SelectedIndex = 1; controls.Controls.Add(resolution);
            Label("Palette °"); controls.Controls.Add(rotation); controls.Controls.Add(save);
            controls.Controls.Add(new Label { Text = "Follow ζ(s)=a; viewport exits remain labeled.", AutoSize = true, Margin = new Padding(12, 7, 0, 0) });
            layout.Controls.Add(controls, 0, 0); layout.Controls.Add(timeline, 0, 1); layout.Controls.Add(picture, 0, 2); layout.Controls.Add(status, 0, 3);
            Controls.Add(layout);
            target.ValueChanged += (_, __) =>
            {
                if (synchronizing) return;
                synchronizing = true; timeline.Value = (int)(target.Value * 1000); synchronizing = false; RequestRender();
            };
            timeline.ValueChanged += (_, __) =>
            {
                if (synchronizing) return;
                synchronizing = true; target.Value = timeline.Value / 1000m; synchronizing = false; RequestRender();
            };
            rotation.ValueChanged += (_, __) => RequestRender(); resolution.SelectedIndexChanged += (_, __) => RequestRender();
            reset.Click += (_, __) => { SetPlaying(false); target.Value = 0; };
            end.Click += (_, __) => { SetPlaying(false); target.Value = 1; };
            play.Click += (_, __) => { if (!playing && target.Value == 1) target.Value = 0; SetPlaying(!playing); };
            animation.Tick += (_, __) =>
            {
                if (!playing || rendering || paths == null) return;
                if (target.Value >= 1) { SetPlaying(false); return; }
                target.Value = Math.Min(1, target.Value + 0.01m);
                if (target.Value >= 1) SetPlaying(false);
            };
            save.Click += (_, __) => SaveFrame();
            picture.MouseMove += (_, e) => Inspect(e.Location);
            picture.MouseLeave += (_, __) => { if (!rendering && displayed != null && displayedVersion == requestedVersion) status.Text = displayed.Report; };
            Shown += async (_, __) =>
            {
                status.Text = "Following three zeros with adaptive predictor/Newton steps and explicit boundary checks…";
                try
                {
                    paths = await Task.Run(() => ZetaContinuationExperiment.ComputePaths());
                    if (IsDisposed || Disposing) return;
                    play.Enabled = true;
                    RequestRender();
                }
                catch (Exception error) { if (!IsDisposed && !Disposing) status.Text = "Continuation failed: " + error.Message; }
            };
        }

        private void SetPlaying(bool value)
        { playing = value; play.Text = value ? "Pause" : "Play"; if (value) animation.Start(); else animation.Stop(); }

        private void RequestRender()
        {
            if (IsDisposed || Disposing || paths == null) return;
            requestedVersion++; save.Enabled = false;
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
                    double a = (double)target.Value, degrees = (double)rotation.Value;
                    int grid = (int)resolution.SelectedItem;
                    status.Text = $"Rendering ζ(s)−a at a={a:F3}; reusing the cached ζ grid…";
                    var frame = await Task.Run(() => ZetaContinuationExperiment.Render(paths, a, grid, degrees));
                    if (IsDisposed || Disposing) { frame.Dispose(); return; }
                    if (version != requestedVersion) { frame.Dispose(); continue; }
                    var old = displayed; displayed = frame; picture.Image = frame.Image; old?.Dispose();
                    displayedVersion = version; status.Text = frame.Report;
                }
            }
            catch (Exception error)
            {
                if (!IsDisposed && !Disposing) { SetPlaying(false); status.Text = "Unable to render: " + error.Message; }
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
            status.Text = ZetaContinuationExperiment.TryMapPixel(x, y, out Complex s)
                ? ZetaContinuationExperiment.DescribePoint(s, displayed.Target) : displayed.Report;
        }

        private void SaveFrame()
        {
            if (rendering || displayed == null || displayedVersion != requestedVersion) return;
            SetPlaying(false);
            using var dialog = new SaveFileDialog { Title = "Save continuation frame and trajectories", Filter = "PNG image (*.png)|*.png", FileName = "zeta-continuation.png", DefaultExt = "png", AddExtension = true, RestoreDirectory = true };
            if (dialog.ShowDialog(this) != DialogResult.OK) return;
            try { ZetaContinuationExperiment.Export(dialog.FileName, displayed); status.Text = "Saved displayed PNG, full trajectory JSON, and text: " + dialog.FileName; }
            catch (Exception error) { MessageBox.Show(this, error.Message, "Save continuation", MessageBoxButtons.OK, MessageBoxIcon.Error); }
        }

        protected override void Dispose(bool disposing)
        {
            if (disposing) { animation.Stop(); animation.Dispose(); picture.Image = null; displayed?.Dispose(); displayed = null; }
            base.Dispose(disposing);
        }
    }
}
