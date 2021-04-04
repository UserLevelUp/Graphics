using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.Data;
using System.Drawing;
using System.Drawing.Text;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using System.Windows.Forms;
using System.Numerics;
using System.Buffers;
using System.Threading;

namespace Graphics
{
    public partial class GraphForm : Form
    {
        public GraphForm()
        {
            InitializeComponent();
        }

        private void Form1_Load(object sender, EventArgs e)
        {

        }

        
        // private variables ... make this more extensible and functional and testable
        private ReadOnlySequence<Point> spts = new ReadOnlySequence<Point>();
        private List<Point> pts = new List<Point>();
        private static Queue<Point> qpts = new System.Collections.Generic.Queue<Point>();
        private int maxX = 0;
        private int maxY = 0;
        private int minX = 0;
        private int minY = 0;
        private bool dequeing_flag = false;


        // Green paint brush... TODO: build based on user selection
        private System.Drawing.SolidBrush myBrush3 = new System.Drawing.SolidBrush(System.Drawing.Color.Green);

        // flags
        private Boolean runIt = false;
        private Boolean breakOut = true; // when set to true it should break out of the next iteration and stop the current plot.  This is not very functional but works

        /// <summary>
        /// panel4_Paint ... change name to GraphicPaint or Layer Paint etc...
        /// </summary>
        /// <param name="sender"></param>
        /// <param name="e"></param>
        private void panel4_Paint(object sender, PaintEventArgs e)
        {
                if (this.runIt == true)
                {
                    while (qpts.Count > 0)
                    {
                        var pt = qpts.Dequeue();
                            e.Graphics.DrawLine(new Pen(myBrush3),
                                pt,
                                new Point(pt.X + 1, pt.Y + 1)
                            );
                    }
                    this.dequeing_flag = false;
                }
        }

        private static Point plotPoint;

        private async Task performFormula()
        {
            // iterates over some plot or formula ... may need to change this to x, y, z etc...
            // needs to use smarter iteration and plots by placing in a thread or threads
            for (int x = 0; x < 1_500_000_000; x++)
            {
                if (this.breakOut == true)
                {
                    break;
                }

                while (this.runIt == false)
                {
                    System.Threading.Thread.Sleep(100);
                }

                // the current offset uses the center of screen plus some number
                var ox = this.panel4.Width / 2 + 1300;
                var oy = this.panel4.Height /2 + 1300;


                // zoom
                var zoom = Math.E;

                // Equations - not very extensible... move equations into a text string then figure out a way to generate these equations dynamically during a plot
                var cos = Complex.Sqrt(zoom * x * 0.00001 * Math.Cos(x * 0.0001));
                var sin = Complex.Sqrt(zoom * x * 0.00001 * Math.Sin(x * 0.0001));

//                cos = new Complex(cos.Real, cos.Imaginary);
//                sin = new Complex(sin.Real, sin.Imaginary);

                // convert the plot during each iteration to a single point to be rendered
                var pt = new Point(
                        ox + (cos.Imaginary == 0 ? (int)(cos.Real * 42) : (int)(cos.Imaginary * 42) * -1),
                        oy + (sin.Imaginary == 0 ? (int)(sin.Real * 42) : (int)(sin.Imaginary * 42) * -1));

                // check that the plot has not already been plotted, otherwise skip or continue to next iteration
                if (plotPoint.X == pt.X && plotPoint.Y == pt.Y)
                    continue;

                // save the current point after testing if it was already plotted last
                // TODO: perhaps store points in a key value pair where the key is a plotted point... if it was already plotted for a given color then move on
                plotPoint.X = pt.X;
                plotPoint.Y = pt.Y;

                // uses a Queue property to save a point 
                // currently its global on this form ... should be more functional
                qpts.Enqueue(new Point(pt.X, pt.Y));

                // after every single iteration that wasn't already plotted it will cause plot to invalidated and updated
                if (x%1 == 0)
                {
                    this.dequeing_flag = true;

                    // move back to the windows form thread to perform windows form operations using the drawing area and the invoke command
                    this.panel4.Invoke(new Action(() =>
                        {
                                panel4.Invalidate(new Rectangle(new Point(pt.X, pt.Y), new Size(2, 2)));
                                panel4.Update();
                        }));
                }
            }

        }

        /// <summary>
        /// When graphing it fires an async task to plot a formula
        /// </summary>
        /// <param name="sender"></param>
        /// <param name="e"></param>
        private void btnGraph_Click(object sender, EventArgs e)
        {
            this.breakOut = !this.breakOut;
            // TODO: Check to see if it broke out.  Create a nother parameter to check...
            System.Threading.Thread.Sleep(1000);

            this.runIt = true;
            _ = Task.Run(async () =>
              {
                  await performFormula();
              });
            
        }

        private void txtZoom_KeyPress(object sender, KeyPressEventArgs e)
        {
            // used code from: https://stackoverflow.com/questions/19761487/how-to-make-a-textbox-accept-only-numbers-and-just-one-decimal-point-in-windows
            if (!(char.IsDigit(e.KeyChar) || e.KeyChar == (char)Keys.Back || e.KeyChar == '.'))
            { e.Handled = true; }
            TextBox txtDecimal = sender as TextBox;
            if (e.KeyChar == '.' && txtDecimal.Text.Contains("."))
            {
                e.Handled = true;
            }
        }

        private void btnPause_Click(object sender, EventArgs e)
        {
            if (this.runIt == true)
            {
                this.runIt = false;
                this.btnPause.Text = "Continue";
            }
            else
            {
                this.runIt = true;
                this.btnPause.Text = "Pause";
            }
        }
    }
}
