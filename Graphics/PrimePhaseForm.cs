using System;
using System.Drawing;
using System.Drawing.Imaging;
using System.Threading.Tasks;
using System.Windows.Forms;

namespace Graphics
{
    // consumer: graph.primes.phase
    internal sealed class PrimePhaseForm : Form
    {
        private readonly NumericUpDown sigma = new NumericUpDown
        {
            Minimum = 1.05m,
            Maximum = 3m,
            Value = 1.2m,
            Increment = 0.05m,
            DecimalPlaces = 2,
            Width = 80
        };

        private readonly ComboBox cutoff = new ComboBox
        {
            DropDownStyle = ComboBoxStyle.DropDownList,
            Width = 84
        };

        private readonly NumericUpDown basisDegrees = new NumericUpDown
        {
            DecimalPlaces = 1,
            Minimum = 0,
            Maximum = 90,
            Value = 0,
            Increment = 15,
            Width = 72
        };

        private readonly ComboBox selectedPrime = new ComboBox
        {
            DropDownStyle = ComboBoxStyle.DropDownList,
            Width = 82,
            MaxDropDownItems = 16,
            IntegralHeight = false,
            DropDownHeight = 320
        };

        private readonly CheckBox reverseOrder = new CheckBox
        {
            Text = "Reverse prime order",
            AutoSize = true,
            Margin = new Padding(0, 5, 14, 0)
        };

        private readonly CheckBox overlayLandmarks = new CheckBox
        {
            Text = "Prime / zeta overlays",
            Checked = true,
            AutoSize = true,
            Margin = new Padding(0, 5, 14, 0)
        };

        private readonly Button unwrapButton = new Button { Text = "Unwrap factors", AutoSize = true };
        private readonly Button renderButton = new Button { Text = "Render", AutoSize = true };
        private readonly Button saveButton = new Button { Text = "Save PNG", AutoSize = true, Enabled = false };
        private readonly FlowLayoutPanel toolbar = new FlowLayoutPanel
        {
            Dock = DockStyle.Fill,
            AutoSize = true,
            AutoSizeMode = AutoSizeMode.GrowAndShrink,
            WrapContents = true,
            Padding = new Padding(12),
            Margin = Padding.Empty
        };

        private readonly PictureBox picture = new PictureBox
        {
            Dock = DockStyle.Fill,
            SizeMode = PictureBoxSizeMode.Zoom,
            BackColor = Color.FromArgb(16, 14, 24),
            Margin = Padding.Empty
        };

        private readonly TextBox reportBox = new TextBox
        {
            Dock = DockStyle.Fill,
            Multiline = true,
            ReadOnly = true,
            ScrollBars = ScrollBars.Vertical,
            BackColor = SystemColors.Window,
            BorderStyle = BorderStyle.None,
            Margin = new Padding(12, 8, 12, 8),
            Text = "Preparing the prime color view."
        };

        private bool rendering;

        public PrimePhaseForm()
        {
            Text = "Prime color laboratory";
            StartPosition = FormStartPosition.CenterParent;
            AutoScaleMode = AutoScaleMode.Dpi;
            ClientSize = new Size(1440, 1000);
            MinimumSize = new Size(1000, 760);
            var available = Screen.FromPoint(Cursor.Position).WorkingArea.Size;
            Size = new Size(Math.Min(Width, available.Width - 32), Math.Min(Height, available.Height - 32));

            cutoff.Items.AddRange(new object[] { 32, 128, 512, 2048 });
            cutoff.SelectedItem = 512;
            UpdatePrimes();
            cutoff.SelectedIndexChanged += (sender, args) => UpdatePrimes();

            AddLabeledControl("Real part σ", sigma);
            AddLabeledControl("Primes up to", cutoff);
            AddLabeledControl("Axis rotation °", basisDegrees);
            AddLabeledControl("Selected prime", selectedPrime);
            toolbar.Controls.Add(reverseOrder);
            toolbar.Controls.Add(overlayLandmarks);
            toolbar.Controls.Add(renderButton);
            toolbar.Controls.Add(saveButton);
            toolbar.Controls.Add(unwrapButton);

            var layout = new TableLayoutPanel
            {
                Dock = DockStyle.Fill,
                ColumnCount = 1,
                RowCount = 3,
                Margin = Padding.Empty,
                Padding = Padding.Empty
            };
            layout.ColumnStyles.Add(new ColumnStyle(SizeType.Percent, 100));
            layout.RowStyles.Add(new RowStyle(SizeType.AutoSize));
            layout.RowStyles.Add(new RowStyle(SizeType.Percent, 100));
            layout.RowStyles.Add(new RowStyle(SizeType.Absolute, 88));
            layout.Controls.Add(toolbar, 0, 0);
            layout.Controls.Add(picture, 0, 1);
            layout.Controls.Add(reportBox, 0, 2);
            Controls.Add(layout);

            renderButton.Click += async (sender, args) => await RenderAsync();
            saveButton.Click += (sender, args) => SaveImage();
            unwrapButton.Click += (sender, args) => ShowUnwrapped();
            Shown += async (sender, args) => await RenderAsync();
            AcceptButton = renderButton;
        }

        private void AddLabeledControl(string text, Control control)
        {
            var group = new FlowLayoutPanel
            {
                AutoSize = true,
                AutoSizeMode = AutoSizeMode.GrowAndShrink,
                WrapContents = false,
                Margin = new Padding(0, 0, 14, 0)
            };
            group.Controls.Add(new Label
            {
                Text = text,
                AutoSize = true,
                Margin = new Padding(0, 6, 6, 0)
            });
            control.Margin = Padding.Empty;
            group.Controls.Add(control);
            toolbar.Controls.Add(group);
        }

        private void UpdatePrimes()
        {
            int previousPrime = selectedPrime.SelectedItem is int prime ? prime : 13;
            int[] primes = PrimePhaseExperiment.Primes((int)cutoff.SelectedItem);
            selectedPrime.BeginUpdate();
            try
            {
                selectedPrime.Items.Clear();
                foreach (int value in primes)
                    selectedPrime.Items.Add(value);
                selectedPrime.SelectedItem = previousPrime;
                if (selectedPrime.SelectedIndex < 0)
                    selectedPrime.SelectedItem = 13;
                if (selectedPrime.SelectedIndex < 0 && selectedPrime.Items.Count > 0)
                    selectedPrime.SelectedIndex = 0;
            }
            finally
            {
                selectedPrime.EndUpdate();
            }
        }

        private async Task RenderAsync()
        {
            if (rendering || IsDisposed || Disposing)
                return;

            double realPart = (double)sigma.Value;
            int primeCutoff = (int)cutoff.SelectedItem;
            double rotation = (double)basisDegrees.Value;
            int prime = (int)selectedPrime.SelectedItem;
            bool reverse = reverseOrder.Checked;
            bool overlay = overlayLandmarks.Checked;
            rendering = true;
            toolbar.Enabled = false;
            reportBox.Text = "Rendering the prime colors…";

            try
            {
                var result = await Task.Run(() =>
                {
                    Bitmap image = PrimePhaseExperiment.Render(realPart, primeCutoff,
                        rotation, prime, reverse, out string report, overlay);
                    return (Image: image, Report: report);
                });

                if (IsDisposed || Disposing)
                {
                    result.Image.Dispose();
                    return;
                }

                Image previous = picture.Image;
                picture.Image = result.Image;
                previous?.Dispose();
                reportBox.Text = result.Report;
            }
            catch (Exception error)
            {
                if (!IsDisposed && !Disposing)
                {
                    reportBox.Text = "The view could not be rendered. " + error.Message;
                    MessageBox.Show(this, error.Message, "Prime color laboratory",
                        MessageBoxButtons.OK, MessageBoxIcon.Error);
                }
            }
            finally
            {
                rendering = false;
                if (!IsDisposed && !Disposing)
                {
                    toolbar.Enabled = true;
                    saveButton.Enabled = picture.Image != null;
                }
            }
        }

        private void ShowUnwrapped()
        {
            double realPart = (double)sigma.Value;
            int prime = (int)selectedPrime.SelectedItem;
            using var preview = new Form
            {
                Text = $"Prime {prime} factors unwrapped",
                StartPosition = FormStartPosition.CenterParent,
                ClientSize = new Size(1320, 900),
                MinimumSize = new Size(900, 640)
            };
            using var imageView = new PictureBox
            {
                Dock = DockStyle.Fill,
                SizeMode = PictureBoxSizeMode.Zoom,
                BackColor = Color.FromArgb(16, 14, 24)
            };
            using var explanation = new TextBox
            {
                Dock = DockStyle.Bottom,
                Height = 90,
                Multiline = true,
                ReadOnly = true,
                ScrollBars = ScrollBars.Vertical,
                Text = "Unwrapping the selected prime…"
            };
            preview.Controls.Add(imageView);
            preview.Controls.Add(explanation);
            preview.Shown += async (sender, args) =>
            {
                try
                {
                    var result = await Task.Run(() =>
                    {
                        Bitmap image = PrimeUnwrap.Render(realPart, prime, out string report);
                        return (Image: image, Report: report);
                    });
                    if (preview.IsDisposed || preview.Disposing)
                    {
                        result.Image.Dispose();
                        return;
                    }
                    imageView.Image = result.Image;
                    explanation.Text = result.Report;
                }
                catch (Exception error)
                {
                    if (!preview.IsDisposed && !preview.Disposing)
                    {
                        explanation.Text = "The factors could not be unwrapped. " + error.Message;
                        MessageBox.Show(preview, error.Message, "Unwrap factors",
                            MessageBoxButtons.OK, MessageBoxIcon.Error);
                    }
                }
            };
            try
            {
                preview.ShowDialog(this);
            }
            finally
            {
                imageView.Image?.Dispose();
                imageView.Image = null;
            }
        }

        private void SaveImage()
        {
            if (picture.Image == null)
                return;

            using var dialog = new SaveFileDialog
            {
                Title = "Save prime color view",
                FileName = "prime-colors.png",
                Filter = "PNG image (*.png)|*.png",
                DefaultExt = "png",
                AddExtension = true,
                RestoreDirectory = true
            };
            if (dialog.ShowDialog(this) != DialogResult.OK)
                return;

            try
            {
                picture.Image.Save(dialog.FileName, ImageFormat.Png);
            }
            catch (Exception error)
            {
                MessageBox.Show(this, error.Message, "Save prime color view",
                    MessageBoxButtons.OK, MessageBoxIcon.Error);
            }
        }

        protected override void Dispose(bool disposing)
        {
            if (disposing)
            {
                picture.Image?.Dispose();
                picture.Image = null;
            }
            base.Dispose(disposing);
        }
    }
}
