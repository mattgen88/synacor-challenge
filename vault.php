<?php



// Move from 0,0 to 3,3 to get 30 at the vault
// In the minimum number of steps
// You can return to a previous room
// You cannot go to 0,0 again
// You cannot go to 3,3 unless it will equal 30

function make_position($position) {
	$dir = "";
	while (TRUE) {
		$new_position = $position;
		if (mt_rand(0,1)===0) {
			// change x
			if (mt_rand(0, 1) === 0) {
				$dir = "NORTH ";
				$new_position[0]++;
			} else {
				$dir = "SOUTH ";
				$new_position[0]--;
			}
		} else {
			// change y
			if (mt_rand(0, 1) === 0) {
				$dir = "EAST ";
				$new_position[1]++;
			} else {
				$dir = "WEST ";
				$new_position[1]--;
			}
		}
		if ($new_position[0] < 0
			|| $new_position[1] < 0
			|| $new_position[1] > 3
			|| $new_position[0] > 3
			|| ($new_position === [0, 0])) {
				continue;
			}
		break;
	}
	if ($new_position !== [3,3]) {
//		echo $dir . ")";
	}
	return $new_position;
}

function explore($max_steps) {
	global $vault;
	$moves = [];
	$position = [0, 0];
	$weight = 22;
	$operator = '';
//	echo "( $weight ";
	while ($position !== [3,3]) {
		$new_position = $position;
		$new_position = make_position($position);
		if ($new_position === [3, 3]) {
//			echo "Dropping out";
			break;
		}
		$moves[] = ['x' => $new_position[0], 'y' => $new_position[1]];
		if (count($moves) > $max_steps) {
			return false;
		}
		$position = $new_position;

		$val = $vault[$position[0]][$position[1]];
		switch ($val) {
			case '+':
				$operator = '+';
//				echo "( $operator ";
			break;
			case '*':
				$operator = '*';
//				echo "( $operator ";
			break;
			case '-':
				$operator = '-';
//				echo "( $operator ";
			break;
			default:
//				echo "( $val ";
				$weight = eval("return $weight $operator $val;");
			break;
		}
	}
//	echo " 1";
	if ($operator === '-') {
		$weight--;
	}
	if ($weight === 30) {
//		echo " = 30\n";
		return $moves;
	}
//	echo "\nFAILS $weight \n";
	return false;
}

function print_steps($result) {
	echo "(0,0) ";
	foreach($result as $step) {
		echo "(" . $step['x'] . "," . $step['y'] . ") ";
	}
	echo "(3,3)\n";
}

$vault = [
	[22, '-', 9, '*'],
	['+', 4, '-', 18],
	[4, '*', 11, '*'],
	['*', 8, '-', 1],
];

$start = [0,0];
$end = [3, 3];
$result = false;
$lowest = 999;
$iterations = 0;
do {
	if ($iterations % 1000 === 0) {
		echo "$iterations \n";
	}
	$result = explore($lowest);
	$steps = count($result);
	if (is_array($result) && $steps < $lowest) {
		$lowest = $steps;
		echo "New lowest found for " . $steps . " steps.\n";
		print_steps($result);
	}
	$iterations++;
}
while (!$result || $steps > 10);
echo "\nTotal iteration " . count($result) . "\n";
//print_r($result);
/*
New lowest found for 13 steps.
(0,0) (1,0) (2,0) (1,0) (2,0) (1,0) (1,1) (1,0) (2,0) (1,0) (1,1) (1,2) (2,2) (3,2) (3,3)
*/
?>
