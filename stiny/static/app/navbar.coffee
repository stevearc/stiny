angular.module('stiny')

.directive('stNavbar', ['CONST', (CONST) ->
  templateUrl: "#{ CONST.URL_PREFIX }/app/navbar.html"
  restrict: 'A'
  replace: true
  controller: 'NavCtrl'
])

.controller('NavCtrl', ['$scope', '$location', 'CONST',
($scope, $location, CONST) ->

])
