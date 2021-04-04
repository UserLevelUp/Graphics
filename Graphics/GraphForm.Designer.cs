
namespace Graphics
{
    partial class GraphForm
    {
        /// <summary>
        ///  Required designer variable.
        /// </summary>
        private System.ComponentModel.IContainer components = null;

        /// <summary>
        ///  Clean up any resources being used.
        /// </summary>
        /// <param name="disposing">true if managed resources should be disposed; otherwise, false.</param>
        protected override void Dispose(bool disposing)
        {
            if (disposing && (components != null))
            {
                components.Dispose();
            }
            base.Dispose(disposing);
        }

        #region Windows Form Designer generated code

        /// <summary>
        ///  Required method for Designer support - do not modify
        ///  the contents of this method with the code editor.
        /// </summary>
        private void InitializeComponent()
        {
			this.panel2 = new System.Windows.Forms.Panel();
			this.panel3 = new System.Windows.Forms.Panel();
			this.panel4 = new System.Windows.Forms.Panel();
			this.comboBox1 = new System.Windows.Forms.ComboBox();
			this.panel5 = new System.Windows.Forms.Panel();
			this.splitContainer1 = new System.Windows.Forms.SplitContainer();
			this.panel1 = new System.Windows.Forms.Panel();
			this.btnClear = new System.Windows.Forms.Button();
			this.btnPause = new System.Windows.Forms.Button();
			this.txtZoom = new System.Windows.Forms.TextBox();
			this.lblZoom = new System.Windows.Forms.Label();
			this.btnGraph = new System.Windows.Forms.Button();
			this.statusStrip1 = new System.Windows.Forms.StatusStrip();
			this.toolStripStatusLabel1 = new System.Windows.Forms.ToolStripStatusLabel();
			this.toolStripStatusLabel2 = new System.Windows.Forms.ToolStripStatusLabel();
			this.panel5.SuspendLayout();
			((System.ComponentModel.ISupportInitialize)(this.splitContainer1)).BeginInit();
			this.splitContainer1.Panel1.SuspendLayout();
			this.splitContainer1.Panel2.SuspendLayout();
			this.splitContainer1.SuspendLayout();
			this.panel1.SuspendLayout();
			this.statusStrip1.SuspendLayout();
			this.SuspendLayout();
			// 
			// panel2
			// 
			this.panel2.Location = new System.Drawing.Point(12, 12);
			this.panel2.Name = "panel2";
			this.panel2.Size = new System.Drawing.Size(416, 78);
			this.panel2.TabIndex = 1;
			// 
			// panel3
			// 
			this.panel3.Anchor = ((System.Windows.Forms.AnchorStyles)(((System.Windows.Forms.AnchorStyles.Top | System.Windows.Forms.AnchorStyles.Left) 
            | System.Windows.Forms.AnchorStyles.Right)));
			this.panel3.AutoSizeMode = System.Windows.Forms.AutoSizeMode.GrowAndShrink;
			this.panel3.Location = new System.Drawing.Point(434, 12);
			this.panel3.Name = "panel3";
			this.panel3.Size = new System.Drawing.Size(1374, 78);
			this.panel3.TabIndex = 3;
			// 
			// panel4
			// 
			this.panel4.Anchor = ((System.Windows.Forms.AnchorStyles)((((System.Windows.Forms.AnchorStyles.Top | System.Windows.Forms.AnchorStyles.Bottom) 
            | System.Windows.Forms.AnchorStyles.Left) 
            | System.Windows.Forms.AnchorStyles.Right)));
			this.panel4.AutoSizeMode = System.Windows.Forms.AutoSizeMode.GrowAndShrink;
			this.panel4.BackColor = System.Drawing.SystemColors.Window;
			this.panel4.Location = new System.Drawing.Point(434, 96);
			this.panel4.Name = "panel4";
			this.panel4.Size = new System.Drawing.Size(1374, 943);
			this.panel4.TabIndex = 2;
			this.panel4.Paint += new System.Windows.Forms.PaintEventHandler(this.panel4_Paint);
			// 
			// comboBox1
			// 
			this.comboBox1.FormattingEnabled = true;
			this.comboBox1.Location = new System.Drawing.Point(31, 58);
			this.comboBox1.Name = "comboBox1";
			this.comboBox1.Size = new System.Drawing.Size(242, 40);
			this.comboBox1.TabIndex = 4;
			// 
			// panel5
			// 
			this.panel5.Anchor = ((System.Windows.Forms.AnchorStyles)(((System.Windows.Forms.AnchorStyles.Top | System.Windows.Forms.AnchorStyles.Bottom) 
            | System.Windows.Forms.AnchorStyles.Left)));
			this.panel5.Controls.Add(this.comboBox1);
			this.panel5.Location = new System.Drawing.Point(3, 3);
			this.panel5.Name = "panel5";
			this.panel5.Size = new System.Drawing.Size(410, 465);
			this.panel5.TabIndex = 1;
			// 
			// splitContainer1
			// 
			this.splitContainer1.Anchor = ((System.Windows.Forms.AnchorStyles)(((System.Windows.Forms.AnchorStyles.Top | System.Windows.Forms.AnchorStyles.Bottom) 
            | System.Windows.Forms.AnchorStyles.Left)));
			this.splitContainer1.Location = new System.Drawing.Point(12, 96);
			this.splitContainer1.Name = "splitContainer1";
			this.splitContainer1.Orientation = System.Windows.Forms.Orientation.Horizontal;
			// 
			// splitContainer1.Panel1
			// 
			this.splitContainer1.Panel1.BackColor = System.Drawing.SystemColors.InactiveCaption;
			this.splitContainer1.Panel1.Controls.Add(this.panel1);
			// 
			// splitContainer1.Panel2
			// 
			this.splitContainer1.Panel2.BackColor = System.Drawing.SystemColors.InactiveCaption;
			this.splitContainer1.Panel2.Controls.Add(this.panel5);
			this.splitContainer1.Size = new System.Drawing.Size(416, 943);
			this.splitContainer1.SplitterDistance = 468;
			this.splitContainer1.TabIndex = 4;
			// 
			// panel1
			// 
			this.panel1.Anchor = ((System.Windows.Forms.AnchorStyles)(((System.Windows.Forms.AnchorStyles.Top | System.Windows.Forms.AnchorStyles.Bottom) 
            | System.Windows.Forms.AnchorStyles.Left)));
			this.panel1.Controls.Add(this.btnClear);
			this.panel1.Controls.Add(this.btnPause);
			this.panel1.Controls.Add(this.txtZoom);
			this.panel1.Controls.Add(this.lblZoom);
			this.panel1.Controls.Add(this.btnGraph);
			this.panel1.Location = new System.Drawing.Point(3, 3);
			this.panel1.Name = "panel1";
			this.panel1.Size = new System.Drawing.Size(410, 462);
			this.panel1.TabIndex = 0;
			// 
			// btnClear
			// 
			this.btnClear.Anchor = ((System.Windows.Forms.AnchorStyles)((System.Windows.Forms.AnchorStyles.Bottom | System.Windows.Forms.AnchorStyles.Left)));
			this.btnClear.Location = new System.Drawing.Point(13, 416);
			this.btnClear.Name = "btnClear";
			this.btnClear.Size = new System.Drawing.Size(139, 46);
			this.btnClear.TabIndex = 4;
			this.btnClear.Text = "Clear";
			this.btnClear.UseVisualStyleBackColor = true;
			this.btnClear.Click += new System.EventHandler(this.btnClear_Click);
			// 
			// btnPause
			// 
			this.btnPause.Location = new System.Drawing.Point(169, 13);
			this.btnPause.Name = "btnPause";
			this.btnPause.Size = new System.Drawing.Size(141, 46);
			this.btnPause.TabIndex = 3;
			this.btnPause.Text = "Pause";
			this.btnPause.UseVisualStyleBackColor = true;
			this.btnPause.Click += new System.EventHandler(this.btnPause_Click);
			// 
			// txtZoom
			// 
			this.txtZoom.Location = new System.Drawing.Point(114, 122);
			this.txtZoom.Name = "txtZoom";
			this.txtZoom.Size = new System.Drawing.Size(196, 39);
			this.txtZoom.TabIndex = 2;
			this.txtZoom.KeyPress += new System.Windows.Forms.KeyPressEventHandler(this.txtZoom_KeyPress);
			// 
			// lblZoom
			// 
			this.lblZoom.AutoSize = true;
			this.lblZoom.Location = new System.Drawing.Point(37, 122);
			this.lblZoom.Name = "lblZoom";
			this.lblZoom.Size = new System.Drawing.Size(82, 32);
			this.lblZoom.TabIndex = 1;
			this.lblZoom.Tag = "Multiplies By";
			this.lblZoom.Text = "Zoom:";
			// 
			// btnGraph
			// 
			this.btnGraph.Location = new System.Drawing.Point(13, 13);
			this.btnGraph.Name = "btnGraph";
			this.btnGraph.Size = new System.Drawing.Size(139, 46);
			this.btnGraph.TabIndex = 0;
			this.btnGraph.Text = "Graph";
			this.btnGraph.UseVisualStyleBackColor = true;
			this.btnGraph.Click += new System.EventHandler(this.btnGraph_Click);
			// 
			// statusStrip1
			// 
			this.statusStrip1.ImageScalingSize = new System.Drawing.Size(32, 32);
			this.statusStrip1.Items.AddRange(new System.Windows.Forms.ToolStripItem[] {
            this.toolStripStatusLabel2,
            this.toolStripStatusLabel1});
			this.statusStrip1.Location = new System.Drawing.Point(0, 1089);
			this.statusStrip1.Name = "statusStrip1";
			this.statusStrip1.Size = new System.Drawing.Size(1820, 42);
			this.statusStrip1.TabIndex = 5;
			this.statusStrip1.Text = "statusStrip1";
			// 
			// toolStripStatusLabel1
			// 
			this.toolStripStatusLabel1.Name = "toolStripStatusLabel1";
			this.toolStripStatusLabel1.Size = new System.Drawing.Size(172, 32);
			this.toolStripStatusLabel1.Text = "StatusMessage";
			// 
			// toolStripStatusLabel2
			// 
			this.toolStripStatusLabel2.Name = "toolStripStatusLabel2";
			this.toolStripStatusLabel2.Size = new System.Drawing.Size(226, 32);
			this.toolStripStatusLabel2.Text = "Command Message";
			// 
			// GraphForm
			// 
			this.AutoScaleDimensions = new System.Drawing.SizeF(13F, 32F);
			this.AutoScaleMode = System.Windows.Forms.AutoScaleMode.Font;
			this.ClientSize = new System.Drawing.Size(1820, 1131);
			this.Controls.Add(this.statusStrip1);
			this.Controls.Add(this.splitContainer1);
			this.Controls.Add(this.panel3);
			this.Controls.Add(this.panel2);
			this.Controls.Add(this.panel4);
			this.Name = "GraphForm";
			this.Text = "Form1";
			this.Load += new System.EventHandler(this.Form1_Load);
			this.panel5.ResumeLayout(false);
			this.splitContainer1.Panel1.ResumeLayout(false);
			this.splitContainer1.Panel2.ResumeLayout(false);
			((System.ComponentModel.ISupportInitialize)(this.splitContainer1)).EndInit();
			this.splitContainer1.ResumeLayout(false);
			this.panel1.ResumeLayout(false);
			this.panel1.PerformLayout();
			this.statusStrip1.ResumeLayout(false);
			this.statusStrip1.PerformLayout();
			this.ResumeLayout(false);
			this.PerformLayout();

        }

        #endregion
        private System.Windows.Forms.Panel panel2;
        private System.Windows.Forms.Panel panel3;
        private System.Windows.Forms.Panel panel4;
        private System.Windows.Forms.ComboBox comboBox1;
        private System.Windows.Forms.Panel panel5;
        private System.Windows.Forms.SplitContainer splitContainer1;
        private System.Windows.Forms.Panel panel1;
        private System.Windows.Forms.Button btnGraph;
        private System.Windows.Forms.StatusStrip statusStrip1;
        private System.Windows.Forms.TextBox txtZoom;
        private System.Windows.Forms.Label lblZoom;
        private System.Windows.Forms.Button btnPause;
        private System.Windows.Forms.Button btnClear;
		private System.Windows.Forms.ToolStripStatusLabel toolStripStatusLabel1;
		private System.Windows.Forms.ToolStripStatusLabel toolStripStatusLabel2;
	}
}

