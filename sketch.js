//#!/usr/bin/env node


const variance = 0.7;
const average = 0;

const N = 100000;

let sum = 0;
for (let i = 0; i < N; i++) {
	// Whitenoise by Box-Muller transform
	const a = Math.random(), b = Math.random();
	const x = Math.sqrt(-2 * Math.log(a)) * Math.sin(2 * Math.PI * b) * variance + average;
	const y = Math.sqrt(-2 * Math.log(a)) * Math.cos(2 * Math.PI * b) * variance + average;
	sum += x * x + y * y;
}

console.log(Math.sqrt(sum / N / 2));

//console.log(Math.sqrt(2 * variance / Math.PI));
