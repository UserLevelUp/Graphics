﻿using System;
using System.Collections.Generic;
using System.Drawing;
using System.Linq;
using System.Runtime.CompilerServices;
using System.Text;
using System.Threading.Tasks;

namespace Graphics.lib.formulas
{
	/// <summary>
	/// Generalized Formula that uses dictionary of formula names to retrieve and plots a point for a formula given x,y,z,t.   
	/// z and t should yield a 2d plane within each func
	/// </summary>
	public class Formula
	{
		// Examples formula
		//a^2 – b^2 = (a – b)(a + b)
		// y = a^2 - b^2
		// (y = a^2 - b^2) 
		// y = x
		// y = mx + b
		// y = 5*sqrt(x)
		// y = x^2
		// y = sin(x)
		// y = cos(x)
		// y = tan(x)

		public Formula() { }


		/// <summary>
		/// Creates a Dictionary formulas given a formula name
		/// Formula name should have some attention to make it unique ... naming conventions for ever more complex derivatives of a given formula with slight 
		/// modifications
		/// 
		/// For an individual it doesn't really matter what they name then.  But when adding to a public repository of formulas it can get more complicated.
		/// 
		/// Have a method to break down any equation so that it can be stated simply given any input data... basically express a single plot programmatically.
		/// This removes having to express it as a full equation with symbols etc... but those sybols can also be expressed.  Each function when created should have a
		/// that fluff inside so we basically don't care how its implemented or where it comes from but only care how we start the process.  It should be relatively 
		/// quick to get a single point expressed for simple equations and may get more complex for complicated equations.
		/// 
		/// Also every returned point will be considered for a given plane on z axis... so if z changes.... it simply means plot it on the plane on the z axis there
		/// The entity that supplied z will have to keep track on which plane they are plotting.. if a given plane ... doesn't yield a result in that plane... simple 
		/// move the plane until it does yield a plot...  Same for time.  At time 0 there should be no plot and a time n there should be a plot if 1 or more
		/// iterations occured during that plot where a point was returned.
		/// </summary>
		/// <param name="initFormulas"></param>
		public Formula(Dictionary<string, Func<double, double, double, double, Point>> initFormulas)
        {
			this.formulas = initFormulas;
        }

		// Indexer for Formula
		// x, y, z, t=time, Point yields some point given a plane living on z and t
		public Func<double, double, double, double, Point> this[string formulaName]
		{
			get { return this.formulas[formulaName]; }
			set { this.formulas.Add(formulaName, value); }
		}

		/// <summary>
		/// So given a formula name and a starting point of x and/or y and/or z and/or t=time return a point
		/// </summary>
		public Dictionary<string, Func<double, double, double, double, Point>> formulas = new Dictionary<string, Func<double, double, double, double, Point>>();

	}


}