// Declare app level module which depends on filters, and services
angular.module('CREM', ['ngResource', 'ngRoute', 'ui.bootstrap', 'ui.date', 'angular-toArrayFilter', 'angular-loading-bar'])
  .config(['$routeProvider', function ($routeProvider) {
    $routeProvider
      .when('/', {
        templateUrl: 'views/home/home.html',
        controller: 'HomeController'})
      .when('/admin', {
        templateUrl: 'views/home/admin.html',
        controller: 'AdminController'})
      .otherwise({redirectTo: '/'});
  }]);
