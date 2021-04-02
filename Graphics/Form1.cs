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
using System.Collections.Immutable;
using System.Buffers;

namespace Graphics
{
    public partial class Form1 : Form
    {
        public Form1()
        {
            InitializeComponent();
        }

        private void Form1_Load(object sender, EventArgs e)
        {

        }

        private ReadOnlySequence<Point> spts = new ReadOnlySequence<Point>();
        private List<Point> pts = new List<Point>();
        private int maxX = 0;
        private int maxY = 0;
        private int minX = 0;
        private int minY = 0;

        private System.Drawing.SolidBrush myBrush3 = new System.Drawing.SolidBrush(System.Drawing.Color.Green);

        private Boolean runIt = false;
        private void panel4_Paint(object sender, PaintEventArgs e)
        {
            if (this.runIt == true)
            {
                pts.ForEach(pt =>
                {
                    e.Graphics.DrawLine(new Pen(myBrush3),
                    plotPoint,
                    new Point(pt.X + 1, pt.Y + 1)
                    );
                });
                pts.Clear();
            }

        }

        private static Point plotPoint;

        private void performFormula()
        {

            // Draw a Point
            for (int i = 0; i < 1000000000; i++)
            {
                if (this.runIt == false)
                {
                    break;
                }
                var ox = 1650;
                var oy = 1650;

                var cos = Complex.Sqrt(ox + 2.718281828 * i * 0.0001 * Math.Cos(i * 0.0001));
                var sin = Complex.Sqrt(oy + 2.718281828 * i * 0.0001 * Math.Sin(i * 0.0001));
                cos = new Complex(cos.Real, cos.Imaginary);
                sin = new Complex(sin.Real, sin.Imaginary);
                var pt = new Point(
                        cos.Imaginary == 0 ? (int)(cos.Real * 42) : (int)(cos.Imaginary * 42) * -1,
                        sin.Imaginary == 0 ? (int)(sin.Real * 42) : (int)(sin.Imaginary * 42) * -1);
                //e.Graphics.DrawLine(new Pen(myBrush3),
                //    pt,
                //    new Point(pt.X + 1, pt.Y + 1)
                //    );
                if (plotPoint.X == pt.X && plotPoint.Y == pt.Y)
                    continue;
                plotPoint.X = pt.X;
                plotPoint.Y = pt.Y;
                pts.Add(pt);
                //this.minX = Math.Min(pt.X, this.minX);
                //this.maxX = Math.Max(pt.X, this.maxX);
                //this.minY = Math.Min(pt.Y, this.minY);
                //this.maxY = Math.Max(pt.Y, this.maxY);

                this.panel4.Invalidate(new Rectangle(pt, new Size(2,2)));
                if (i%10000 == 0)
                {
                    this.panel4.Update();
                }
            }
        }

        private void btnGraph_Click(object sender, EventArgs e)
        {
            this.runIt = true;
            this.performFormula();
        }
    }
}
