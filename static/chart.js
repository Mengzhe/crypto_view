function createSimpleSwitcher(items, activeItem, activeItemChangedCallback) {
	var switcherElement = document.createElement('div');
	switcherElement.classList.add('switcher');

	var intervalElements = items.map(function(item) {
		var itemEl = document.createElement('button');
		itemEl.innerText = item;
		itemEl.classList.add('switcher-item');
		itemEl.classList.toggle('switcher-active-item', item === activeItem);
		itemEl.addEventListener('click', function() {
			onItemClicked(item);
		});
		switcherElement.appendChild(itemEl);
		return itemEl;
	});

	function onItemClicked(item) {
		if (item === activeItem) {
			return;
		}

		intervalElements.forEach(function(element, index) {
			element.classList.toggle('switcher-active-item', items[index] === item);
		});

		activeItem = item;

		activeItemChangedCallback(item);
	}

	return switcherElement;
}

var switcherElement = createSimpleSwitcher(['es-ES', 'en-US', 'ja-JP'], 'en-US', function(locale) {
	chart.applyOptions({
		localization: {
			locale: locale,
      dateFormat: 'ja-JP' === locale ? 'yyyy-MM-dd' : 'dd MMM \'yy',
		},
	});
});

//var chartElement = document.createElement('div');
var chartElement = document.createElement('chart');

var chart = LightweightCharts.createChart(chartElement, {
	width: 600,
  height: 300,
	localization: {
		locale: 'en-US',
	},
});

document.body.appendChild(chartElement);
document.body.appendChild(switcherElement);

var lineSeries = chart.addLineSeries();

lineSeries.setData([
	{ time: '2018-10-17', value: 52.89 },
	{ time: '2018-10-22', value: 51.65 },
	{ time: '2018-10-23', value: 51.56 },
	{ time: '2018-10-24', value: 50.19 },
	{ time: '2018-10-25', value: 51.86 },
	{ time: '2018-10-26', value: 51.25 },
]);