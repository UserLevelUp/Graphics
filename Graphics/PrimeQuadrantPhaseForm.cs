using System;
using System.Drawing;
using System.Drawing.Imaging;
using System.Threading.Tasks;
using System.Windows.Forms;

namespace Graphics
{
    // consumer: graph.primes.quadrant_phase
    internal sealed class PrimeQuadrantPhaseForm : Form
    {
        private readonly NumericUpDown candidate = new NumericUpDown { Minimum = 0, Maximum = PrimeQuadrantPhaseExperiment.MaximumCandidate, Value = 97, Width = 110 };
        private readonly NumericUpDown rotation = new NumericUpDown { Minimum = -360, Maximum = 360, DecimalPlaces = 1, Increment = 15, Width = 88 };
        private readonly PictureBox picture = new PictureBox { Dock = DockStyle.Fill, SizeMode = PictureBoxSizeMode.Zoom, BackColor = Color.FromArgb(13, 18, 30) };
        private readonly Button render = new Button { Text = "Render", AutoSize = true };
        private readonly Button save = new Button { Text = "Save PNG", AutoSize = true, Enabled = false };
        private readonly Label status = new Label { Dock = DockStyle.Fill, AutoSize = true, Padding = new Padding(12, 7, 12, 7) };
        private readonly FlowLayoutPanel toolbar = new FlowLayoutPanel { AutoSize = true, Dock = DockStyle.Fill, Padding = new Padding(12), WrapContents = true };
        private bool rendering;

        internal PrimeQuadrantPhaseForm()
        {
            Text = "Exact quadrant prime laboratory";
            AutoScaleMode = AutoScaleMode.Dpi;
            StartPosition = FormStartPosition.CenterScreen;
            ClientSize = new Size(1440, 900);
            MinimumSize = new Size(950, 650);
            Size available = Screen.FromPoint(Cursor.Position).WorkingArea.Size;
            Size = new Size(Math.Min(Width, available.Width - 32), Math.Min(Height, available.Height - 32));
            AddControl("Candidate", candidate);
            AddControl("View rotation °", rotation);
            toolbar.Controls.Add(render);
            toolbar.Controls.Add(save);
            foreach (int n in new[] { 4, 96, 97 })
            {
                int target = n;
                var button = new Button { Text = "Try " + n, AutoSize = true };
                button.Click += async (sender, args) => { candidate.Value = target; await RenderAsync(); };
                toolbar.Controls.Add(button);
            }
            var layout = new TableLayoutPanel { Dock = DockStyle.Fill, ColumnCount = 1, RowCount = 3, Margin = Padding.Empty };
            layout.ColumnStyles.Add(new ColumnStyle(SizeType.Percent, 100));
            layout.RowStyles.Add(new RowStyle(SizeType.AutoSize));
            layout.RowStyles.Add(new RowStyle(SizeType.Percent, 100));
            layout.RowStyles.Add(new RowStyle(SizeType.AutoSize));
            layout.Controls.Add(toolbar, 0, 0);
            layout.Controls.Add(picture, 0, 1);
            layout.Controls.Add(status, 0, 2);
            Controls.Add(layout);
            render.Click += async (sender, args) => await RenderAsync();
            save.Click += (sender, args) => {
                if (picture.Image == null) return;
                using var dialog = new SaveFileDialog { Filter = "PNG image|*.png", FileName = "prime-quadrant-phase.png" };
                if (dialog.ShowDialog(this) == DialogResult.OK) picture.Image.Save(dialog.FileName, ImageFormat.Png);
            };
            Shown += async (sender, args) => await RenderAsync();
            AcceptButton = render;
        }

        private void AddControl(string label, Control control)
        {
            toolbar.Controls.Add(new Label { Text = label, AutoSize = true, Margin = new Padding(4, 7, 6, 0) });
            toolbar.Controls.Add(control);
        }

        private async Task RenderAsync()
        {
            if (rendering || IsDisposed || Disposing) return;
            int n = (int)candidate.Value;
            double angle = (double)rotation.Value;
            rendering = true;
            toolbar.Enabled = false;
            status.Text = "Computing the exact modular product and its quadrant…";
            try
            {
                Bitmap image = await Task.Run(() => PrimeQuadrantPhaseExperiment.Render(n, angle));
                if (IsDisposed || Disposing) { image.Dispose(); return; }
                Image previous = picture.Image;
                picture.Image = image;
                previous?.Dispose();
                PrimeQuadrantPhaseExperiment.Sample sample = PrimeQuadrantPhaseExperiment.Evaluate(n, angle);
                status.Text = n < 2 ? "0 and 1 have no Wilson phase and are neither prime nor composite."
                    : $"n={n}: {sample.classification}; R={sample.residue}; exact F=({sample.x},{sample.y}); canonical quadrant {sample.quadrant}. View rotation changes neither the coordinates nor the result.";
            }
            catch (Exception error)
            {
                if (!IsDisposed && !Disposing) status.Text = "Could not render: " + error.Message;
            }
            finally
            {
                rendering = false;
                if (!IsDisposed && !Disposing) { toolbar.Enabled = true; save.Enabled = picture.Image != null; }
            }
        }

        protected override void Dispose(bool disposing)
        {
            if (disposing) { picture.Image?.Dispose(); picture.Image = null; }
            base.Dispose(disposing);
        }
    }
}
